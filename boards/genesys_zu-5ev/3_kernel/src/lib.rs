#![no_std]
extern crate alloc;
mod rpc;
use core::cell::UnsafeCell;
use core::{
    alloc::{GlobalAlloc, Layout},
    ptr, slice,
};
use cslice::CSlice;
use linked_list_allocator::Heap as ListHeap;
const MB: usize = 0x200ff000;
const INPUT: usize = 0x21000000;
const MAX_INPUT: usize = 1024 * 1024;
const BODY: usize = MB + 256;
const BODY_MAX: usize = 4096;
const HEAP_SIZE: usize = 1024 * 1024;
#[repr(align(4096))]
struct Heap([u8; HEAP_SIZE]);
static mut HEAP: Heap = Heap([0; HEAP_SIZE]);
// Exclusively owned by CPU1; CPU0 never accesses allocator internals.
struct WorkerAllocator(UnsafeCell<ListHeap>);
unsafe impl Sync for WorkerAllocator {}
unsafe impl GlobalAlloc for WorkerAllocator {
    unsafe fn alloc(&self, l: Layout) -> *mut u8 {
        (&mut *self.0.get())
            .allocate_first_fit(l)
            .map_or(ptr::null_mut(), |p| p.as_ptr())
    }
    unsafe fn dealloc(&self, p: *mut u8, l: Layout) {
        (&mut *self.0.get()).deallocate(core::ptr::NonNull::new_unchecked(p), l);
    }
}
#[global_allocator]
static ALLOCATOR: WorkerAllocator = WorkerAllocator(UnsafeCell::new(ListHeap::empty()));
static KERNEL_ALLOCATOR: WorkerAllocator = WorkerAllocator(UnsafeCell::new(ListHeap::empty()));
unsafe fn reset_kernel_heap() {
    *KERNEL_ALLOCATOR.0.get() = ListHeap::empty();
    (&mut *KERNEL_ALLOCATOR.0.get()).init(
        ptr::addr_of_mut!(HEAP.0).cast::<u8>().add(HEAP_SIZE / 2),
        HEAP_SIZE / 2,
    );
}
unsafe extern "C" fn malloc(size: usize) -> *mut u8 {
    let total = match size.checked_add(8) {
        Some(v) => v,
        None => fail(b"kernel allocation overflow"),
    };
    let layout = match Layout::from_size_align(total, 8) {
        Ok(v) => v,
        Err(_) => fail(b"kernel allocation layout"),
    };
    let base = KERNEL_ALLOCATOR.alloc(layout);
    if base.is_null() {
        fail(b"kernel heap exhausted");
    }
    ptr::write(base.cast::<usize>(), total);
    base.add(8)
}
unsafe extern "C" fn free(p: *mut u8) {
    if !p.is_null() {
        let base = p.sub(8);
        let size = ptr::read(base.cast::<usize>());
        KERNEL_ALLOCATOR.dealloc(base, Layout::from_size_align_unchecked(size, 8));
    }
}
static mut COMMAND_SEQ: u32 = 0;
static mut EVENT_SEQ: u32 = 0;
static mut RETURN_TAG: u8 = b'n';
static mut NOW: i64 = 0;
extern "C" {
    fn worker_uart(s: *const u8, n: usize);
    fn worker_counter() -> i64;
    fn worker_rtio_init();
}
unsafe fn rd(off: usize) -> u32 {
    ptr::read_volatile((MB + off) as *const u32)
}
unsafe fn wr(off: usize, v: u32) {
    ptr::write_volatile((MB + off) as *mut u32, v);
}
fn barrier() {
    unsafe {
        core::arch::asm!("dsb sy", options(nostack));
    }
}
fn publish(status: u32, bytes: &[u8]) {
    if bytes.len() > BODY_MAX {
        fail(b"worker event overflow");
    }
    unsafe {
        for (i, b) in bytes.iter().enumerate() {
            ptr::write_volatile((BODY + i) as *mut u8, *b);
        }
        wr(68, status);
        wr(72, bytes.len() as u32);
        barrier();
        EVENT_SEQ = EVENT_SEQ.wrapping_add(1);
        wr(64, EVENT_SEQ);
        barrier();
        core::arch::asm!("sev", options(nostack));
    }
}
fn command() -> u32 {
    loop {
        unsafe {
            let seq = rd(0);
            if seq != COMMAND_SEQ {
                barrier();
                COMMAND_SEQ = seq;
                return rd(4);
            }
            core::arch::asm!("wfe", options(nostack));
        }
    }
}
fn fail(message: &[u8]) -> ! {
    unsafe {
        worker_uart(message.as_ptr(), message.len());
    }
    publish(7, message);
    loop {
        unsafe {
            core::arch::asm!("wfe", options(nostack));
        }
    }
}
#[panic_handler]
fn panic(_: &core::panic::PanicInfo) -> ! {
    fail(b"kernel worker panic; restart CPU1 required")
}
#[no_mangle]
pub extern "C" fn worker_trap() -> ! {
    fail(b"kernel hardware exception; restart CPU1 required")
}
#[no_mangle]
pub extern "C" fn rust_eh_personality() {
    fail(b"unsupported Rust exception")
}
fn word(bytes: &[u8], off: usize) -> Option<u32> {
    Some(u32::from_le_bytes(
        bytes.get(off..off.checked_add(4)?)?.try_into().ok()?,
    ))
}
// Bounds gate for trusted locally compiled ELF before entering the upstream loader.
fn valid_elf(b: &[u8]) -> bool {
    if b.len() < 52 || b.get(..7) != Some(b"\x7fELF\x01\x01\x01") || b[16..20] != [3, 0, 40, 0] {
        return false;
    }
    let ph = word(b, 28).unwrap_or(u32::MAX) as usize;
    let sh = word(b, 32).unwrap_or(u32::MAX) as usize;
    let pn = u16::from_le_bytes([b[44], b[45]]) as usize;
    let sn = u16::from_le_bytes([b[48], b[49]]) as usize;
    if ph % 4 != 0
        || sh % 4 != 0
        || b[42..44] != [32, 0]
        || b[46..48] != [40, 0]
        || pn == 0
        || pn > 64
        || sn > 512
    {
        return false;
    }
    if ph.checked_add(pn * 32).map_or(true, |v| v > b.len())
        || sh.checked_add(sn * 40).map_or(true, |v| v > b.len())
    {
        return false;
    }
    for i in 0..pn {
        let p = ph + i * 32;
        let off = word(b, p + 4).unwrap() as usize;
        let va = word(b, p + 8).unwrap() as usize;
        let file = word(b, p + 16).unwrap() as usize;
        let mem = word(b, p + 20).unwrap() as usize;
        let align = word(b, p + 28).unwrap() as usize;
        if off.checked_add(file).map_or(true, |v| v > b.len())
            || va
                .checked_add(mem)
                .map_or(true, |v| v > HEAP_SIZE / 2 - 8192)
        {
            return false;
        }
        if word(b, p).unwrap() == 1 && (file > mem || !align.is_power_of_two() || align > 4096) {
            return false;
        }
    }
    for i in 0..sn {
        let p = sh + i * 40;
        let off = word(b, p + 16).unwrap() as usize;
        let size = word(b, p + 20).unwrap() as usize;
        if word(b, p + 4).unwrap() != 8 && off.checked_add(size).map_or(true, |v| v > b.len()) {
            return false;
        }
    }
    true
}
#[no_mangle]
pub extern "C" fn worker_main() -> ! {
    unsafe {
        (&mut *ALLOCATOR.0.get()).init(ptr::addr_of_mut!(HEAP.0).cast::<u8>(), HEAP_SIZE / 2);
        reset_kernel_heap();
    }
    let mut library: Option<dyld::Library> = None;
    unsafe {
        COMMAND_SEQ = rd(0);
        EVENT_SEQ = 0;
    }
    publish(1, b"A53 AArch32 worker ready; no TTL exports yet");
    loop {
        match command() {
            1 => {
                drop(library.take());
                unsafe {
                    reset_kernel_heap();
                }
                let n = unsafe { rd(8) as usize };
                let bytes = unsafe { slice::from_raw_parts(INPUT as *const u8, n.min(MAX_INPUT)) };
                if n > MAX_INPUT || !valid_elf(bytes) {
                    publish(3, b"invalid or oversized ARM32 shared ELF");
                    continue;
                }
                match dyld::load(bytes, &resolve) {
                    Ok(lib) if lib.lookup(b"__modinit__").is_some() => {
                        library = Some(lib);
                        publish(2, b"");
                    }
                    Ok(_) => publish(3, b"missing __modinit__ entry"),
                    Err(e) => {
                        use alloc::format;
                        let msg = format!("{}", e);
                        publish(3, msg.as_bytes());
                    }
                }
            }
            2 => {
                if let Some(ref lib) = library {
                    let entry = lib.lookup(b"__modinit__").unwrap();
                    let run: extern "C" fn() = unsafe { core::mem::transmute(entry as usize) };
                    run();
                    publish(4, &[0]); // No RTIO outputs enabled, hence no async output errors.
                } else {
                    publish(7, b"no loaded kernel");
                }
            }
            _ => publish(7, b"unexpected worker command"),
        }
    }
}
struct Writer {
    n: usize,
}
#[derive(Debug)]
struct Full;
impl core::fmt::Display for Full {
    fn fmt(&self, f: &mut core::fmt::Formatter<'_>) -> core::fmt::Result {
        f.write_str("RPC event buffer full")
    }
}
impl core::error::Error for Full {}
impl embedded_io::Error for Full {
    fn kind(&self) -> embedded_io::ErrorKind {
        embedded_io::ErrorKind::Other
    }
}
impl embedded_io::ErrorType for Writer {
    type Error = Full;
}
impl embedded_io::Write for Writer {
    fn write(&mut self, b: &[u8]) -> Result<usize, Full> {
        if self.n + b.len() > BODY_MAX - 1 {
            return Err(Full);
        }
        unsafe {
            for (i, v) in b.iter().enumerate() {
                ptr::write_volatile((BODY + 1 + self.n + i) as *mut u8, *v);
            }
        }
        self.n += b.len();
        Ok(b.len())
    }
    fn flush(&mut self) -> Result<(), Full> {
        Ok(())
    }
}
fn rpc_send_common(is_async: bool, service: u32, tag: &CSlice<u8>, data: *const *const ()) {
    let (_, ret) = rpc::tag::split_tag(tag.as_ref());
    if ret.len() != 1 || !b"nbiIuUf".contains(&ret[0]) {
        fail(b"unsupported RPC return type");
    }
    unsafe {
        RETURN_TAG = ret[0];
        ptr::write_volatile(BODY as *mut u8, is_async as u8);
    }
    let mut out = Writer { n: 0 };
    if rpc::send_args(&mut out, service, tag.as_ref(), data, true).is_err() {
        fail(b"RPC packet exceeds 4096 bytes");
    }
    // Serialized bytes already occupy the event body; publish without copying.
    unsafe {
        wr(68, if is_async { 5 } else { 6 });
        wr(72, (out.n + 1) as u32);
        barrier();
        EVENT_SEQ = EVENT_SEQ.wrapping_add(1);
        wr(64, EVENT_SEQ);
        barrier();
        core::arch::asm!("sev", options(nostack));
    }
    if is_async {
        if command() != 3 {
            fail(b"RPC async acknowledgement missing");
        }
    }
}
extern "C" fn rpc_send(service: u32, tag: &CSlice<u8>, data: *const *const ()) {
    rpc_send_common(false, service, tag, data);
}
extern "C" fn rpc_send_async(service: u32, tag: &CSlice<u8>, data: *const *const ()) {
    rpc_send_common(true, service, tag, data);
}
extern "C" fn rpc_recv(slot: *mut ()) -> usize {
    if command() != 4 {
        fail(b"RPC return or exception unsupported");
    }
    let n = unsafe { rd(8) as usize };
    if n > BODY_MAX {
        fail(b"RPC return too large");
    }
    let bytes = unsafe { slice::from_raw_parts(INPUT as *const u8, n) };
    let mut reader = io::Cursor::new(bytes);
    let tag = unsafe { RETURN_TAG };
    if rpc::recv_return(&mut reader, &[tag], slot, &mut |_| {
        fail(b"nested RPC return unsupported")
    })
    .is_err()
    {
        fail(b"RPC return decode failed");
    }
    0
}
extern "C" fn rtio_init() {
    unsafe {
        worker_rtio_init();
    }
}
extern "C" fn rtio_get_counter() -> i64 {
    unsafe { worker_counter() }
}
extern "C" fn at_mu(t: i64) {
    unsafe {
        NOW = t;
    }
}
extern "C" fn now_mu() -> i64 {
    unsafe { NOW }
}
extern "C" fn delay_mu(t: i64) {
    unsafe {
        NOW = NOW.wrapping_add(t);
    }
}
extern "C" fn unsupported() {
    fail(b"kernel exception/unwind unsupported; restart CPU1 required");
}
fn resolve(name: &[u8]) -> Option<u32> {
    macro_rules! sym {($($s:ident),*) => {$(if name==stringify!($s).as_bytes() {return Some($s as usize as u32);})*};}
    sym!(
        rpc_send,
        rpc_send_async,
        rpc_recv,
        rtio_init,
        rtio_get_counter,
        at_mu,
        now_mu,
        delay_mu,
        malloc,
        free
    );
    if name == b"__nac3_personality" || name == b"__nac3_resume" {
        return Some(unsupported as usize as u32);
    }
    None
}
