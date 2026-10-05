#![no_std]
#![no_main]

use aarch64_cpu::registers::{CNTFRQ_EL0, CNTPCT_EL0, CurrentEL, ESR_EL1, FAR_EL1, Readable};
use adacore_zynqmp::uart::Write;
use core::arch::asm;
use core::ptr::{addr_of_mut, read_volatile, write_volatile};

adacore_zynqmp::entry!(bringup);

#[repr(align(64))]
struct Scratch([u64; 16384]);
static mut SCRATCH: Scratch = Scratch([0; 16384]);

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
    writeln!(
        uart,
        "BRINGUP COMPLETE: uart-tx, timer-poll, bounded-ddr; IRQ/Ethernet/ARTIQ pending\r"
    )
    .unwrap();
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
