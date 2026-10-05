#![no_std]
#![no_main]

use aarch64_cpu::registers::{
    CNTFRQ_EL0, CNTP_CTL_EL0, CNTP_TVAL_EL0, CNTPCT_EL0, CurrentEL, ESR_EL1, FAR_EL1, Readable,
    Writeable,
};
use adacore_zynqmp::uart::{Read, Write};
use arm_gic::{IntId, Trigger, gicv2::GicV2};
use core::arch::asm;
use core::ptr::{addr_of_mut, read_volatile, write_volatile};
use core::sync::atomic::{AtomicU64, Ordering};

adacore_zynqmp::entry!(bringup);

#[repr(align(64))]
struct Scratch([u64; 16384]);
static mut SCRATCH: Scratch = Scratch([0; 16384]);
static IRQ_COUNT: AtomicU64 = AtomicU64::new(0);
static IRQ_LAST: AtomicU64 = AtomicU64::new(u64::MAX);

fn gic() -> GicV2<'static> {
    // No foreground driver exists while IRQs are unmasked.
    unsafe { GicV2::new(0xF9010000 as *mut _, 0xF9020000 as *mut _) }
}

fn timer_interrupt_test() -> bool {
    unsafe {
        asm!("msr daifset, #2", "isb");
    }
    {
        let mut controller = gic();
        controller.setup();
        controller.enable_all_interrupts(false);
        controller.set_interrupt_priority(IntId::ppi(14), 0x80);
        controller.set_trigger(IntId::ppi(14), Trigger::Level);
        if controller.enable_interrupt(IntId::ppi(14), true).is_err() {
            return false;
        }
    }
    let frequency = CNTFRQ_EL0.get();
    CNTP_TVAL_EL0.set(frequency / 100);
    CNTP_CTL_EL0.set(1);
    let deadline = CNTPCT_EL0.get() + frequency;
    unsafe {
        asm!("msr daifclr, #2", "isb");
    }
    while IRQ_COUNT.load(Ordering::Acquire) == 0 && CNTPCT_EL0.get() < deadline {
        core::hint::spin_loop();
    }
    unsafe {
        asm!("msr daifset, #2", "isb");
    }
    CNTP_CTL_EL0.set(0);
    gic().enable_interrupt(IntId::ppi(14), false).unwrap();
    IRQ_COUNT.load(Ordering::Acquire) == 1 && IRQ_LAST.load(Ordering::Acquire) == 30
}

#[unsafe(no_mangle)]
extern "C" fn _irq_handler() {
    let mut controller = gic();
    if let Some(id) = controller.get_and_acknowledge_interrupt() {
        CNTP_CTL_EL0.set(0);
        IRQ_LAST.store(u32::from(id) as u64, Ordering::Release);
        IRQ_COUNT.fetch_add(1, Ordering::Release);
        controller.end_interrupt(id);
    }
}

fn halt() -> ! {
    loop {
        aarch64_cpu::asm::wfe();
    }
}

fn bringup() {
    let mut uart = unsafe { adacore_zynqmp::uart::uart0() };
    writeln!(uart, "GENESYS-ZU A53 bringup; diagnostic, not ARTIQ\r").unwrap();
    writeln!(uart, "TEST uart PASS (TX only; host must verify RX)\r").unwrap();
    writeln!(
        uart,
        "REG CurrentEL={:#x} CNTFRQ={}\r",
        CurrentEL.get(),
        CNTFRQ_EL0.get()
    )
    .unwrap();
    let before = CNTPCT_EL0.get();
    for _ in 0..100000 {
        core::hint::spin_loop();
    }
    let after = CNTPCT_EL0.get();
    if after <= before || CNTFRQ_EL0.get() == 0 {
        writeln!(uart, "TEST timer FAIL\r").unwrap();
        halt();
    }
    writeln!(
        uart,
        "TEST timer PASS delta={} (polling only)\r",
        after - before
    )
    .unwrap();

    // Test only application-owned DDR. Flush dirty cache lines to DDR, then
    // invalidate them, so reading back cannot just validate the CPU cache.
    let base = unsafe { addr_of_mut!(SCRATCH.0).cast::<u64>() };
    for pattern in [0u64, u64::MAX, 0xAAAAAAAAAAAAAAAA, 0x5555555555555555] {
        unsafe {
            for i in 0..16384 {
                write_volatile(base.add(i), pattern ^ (i as u64));
            }
            for i in (0..16384).step_by(8) {
                asm!("dc cvac, {0}", in(reg) base.add(i));
            }
            asm!("dsb sy");
            for i in (0..16384).step_by(8) {
                asm!("dc ivac, {0}", in(reg) base.add(i));
            }
            asm!("dsb sy", "isb");
            for i in 0..16384 {
                let expected = pattern ^ (i as u64);
                let actual = read_volatile(base.add(i));
                if actual != expected {
                    writeln!(
                        uart,
                        "TEST ddr FAIL address={:#x} expected={:#x} actual={:#x}\r",
                        base.add(i) as usize,
                        expected,
                        actual
                    )
                    .unwrap();
                    halt();
                }
            }
        }
    }
    writeln!(
        uart,
        "TEST ddr PASS bytes=131072 patterns=4 cache-flushed\r"
    )
    .unwrap();
    let irq = timer_interrupt_test();
    writeln!(
        uart,
        "TEST interrupts {} count={} id={}\r",
        if irq { "PASS" } else { "FAIL" },
        IRQ_COUNT.load(Ordering::Acquire),
        IRQ_LAST.load(Ordering::Acquire)
    )
    .unwrap();
    writeln!(uart, "UART ECHO READY\r").unwrap();
    let mut ping = [0u8; 4];
    let mut received = 0;
    let deadline = CNTPCT_EL0.get() + 5 * CNTFRQ_EL0.get();
    while received < ping.len() && CNTPCT_EL0.get() < deadline {
        received += uart.read(&mut ping[received..]).unwrap();
    }
    if &ping == b"PING" {
        writeln!(uart, "PONG\r").unwrap();
        writeln!(uart, "TEST uart_rx PASS\r").unwrap();
    } else {
        writeln!(uart, "TEST uart_rx NOT_RUN received={}\r", received).unwrap();
    }
    writeln!(uart, "BRINGUP COMPLETE: Ethernet/ARTIQ pending\r").unwrap();
    halt();
}

#[unsafe(no_mangle)]
extern "C" fn _sync_handler() -> ! {
    let mut uart = unsafe { adacore_zynqmp::uart::uart0() };
    let _ = writeln!(
        uart,
        "EXCEPTION ESR_EL1={:#x} FAR_EL1={:#x}\r",
        ESR_EL1.get(),
        FAR_EL1.get()
    );
    halt()
}

#[panic_handler]
fn panic(info: &core::panic::PanicInfo) -> ! {
    let mut uart = unsafe { adacore_zynqmp::uart::uart0() };
    let _ = writeln!(uart, "PANIC {info}\r");
    halt()
}
