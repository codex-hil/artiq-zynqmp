#![no_std]
extern crate alloc;
use core::alloc::{GlobalAlloc, Layout};
use core::sync::atomic::{AtomicUsize, Ordering};

// Single-core, single-kernel test allocator. Not a production allocator.
#[repr(align(4096))]
struct Heap([u8; 262144]);
static mut HEAP: Heap = Heap([0; 262144]);
static NEXT: AtomicUsize = AtomicUsize::new(0);
struct Bump;
unsafe impl GlobalAlloc for Bump {
    unsafe fn alloc(&self, layout: Layout) -> *mut u8 {
        let used = NEXT.load(Ordering::Relaxed);
        let offset = (used + layout.align() - 1) & !(layout.align() - 1);
        if offset + layout.size() > 262144 {
            return core::ptr::null_mut();
        }
        NEXT.store(offset + layout.size(), Ordering::Relaxed);
        core::ptr::addr_of_mut!(HEAP.0).cast::<u8>().add(offset)
    }
    unsafe fn dealloc(&self, _: *mut u8, _: Layout) {}
}
#[global_allocator]
static ALLOCATOR: Bump = Bump;
extern "C" {
    fn resolve_name(name: *const u8, size: usize) -> u32;
    fn probe_fail() -> !;
}
#[panic_handler]
fn panic(_: &core::panic::PanicInfo) -> ! {
    unsafe { probe_fail() }
}

// ELF headers are read as words by the upstream ARM loader. Real A53 with
// MMU disabled rejects unaligned device-memory loads (QEMU allowed them).
#[repr(align(4))]
struct KernelBytes<const N: usize>([u8; N]);
static KERNEL: KernelBytes<{ include_bytes!(env!("KERNEL_ELF")).len() }> =
    KernelBytes(*include_bytes!(env!("KERNEL_ELF")));

#[no_mangle]
pub extern "C" fn execute_kernel() {
    let bytes = &KERNEL.0;
    let library = dyld::load(bytes, &|name| {
        let address = unsafe { resolve_name(name.as_ptr(), name.len()) };
        if address == 0 {
            None
        } else {
            Some(address)
        }
    })
    .unwrap();
    let entry = library.lookup(b"__modinit__").unwrap();
    let run: extern "C" fn() = unsafe { core::mem::transmute(entry as usize) };
    run();
}
