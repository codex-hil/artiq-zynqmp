//! ZynqMP adapters for the preserved M-Labs exception implementation.
use crate::eh_artiq::{Exception, StackPointerBacktrace};

use cslice::CSlice;
pub static mut KERNEL_IMAGE: *const dyld::Library = core::ptr::null();

#[no_mangle]
extern "C" fn dl_unwind_find_exidx(pc: *const u32, len: *mut u32) -> *const u32 {
    extern "C" {
        static __text_start: u32;
        static __text_end: u32;
        static __exidx_start: u32;
        static __exidx_end: u32;
    }
    unsafe {
        if pc >= core::ptr::addr_of!(__text_start) && pc < core::ptr::addr_of!(__text_end) {
            let start = core::ptr::addr_of!(__exidx_start);
            *len = (core::ptr::addr_of!(__exidx_end) as usize - start as usize) as u32 / 8;
            start
        } else if let Some(lib) = KERNEL_IMAGE.as_ref() {
            let a = lib.image.data.as_ptr() as usize;
            if (pc as usize) >= a && (pc as usize) < a + lib.image.data.len() {
                let entries = lib.exidx();
                *len = entries.len() as u32;
                entries.as_ptr().cast()
            } else {
                *len = 0;
                core::ptr::null()
            }
        } else {
            *len = 0;
            core::ptr::null()
        }
    }
}
struct Packet {
    n: usize,
}
impl Packet {
    fn push(&mut self, b: u8) {
        if self.n >= crate::BODY_MAX {
            crate::fail(b"exception packet exceeds 4096 bytes");
        }
        unsafe {
            core::ptr::write_volatile((crate::BODY + self.n) as *mut u8, b);
        }
        self.n += 1;
    }
    fn extend_from_slice(&mut self, bytes: &[u8]) {
        for &b in bytes {
            self.push(b);
        }
    }
}
fn u32le(out: &mut Packet, v: u32) {
    out.extend_from_slice(&v.to_le_bytes());
}
fn string(out: &mut Packet, s: CSlice<'_, u8>) {
    u32le(out, s.len() as u32);
    if s.len() == usize::MAX {
        u32le(out, s.as_ptr() as u32);
    } else {
        out.extend_from_slice(s.as_ref());
    }
}
pub mod core1 {
    use super::*;
    /// Wire layout matches upstream runtime/comms.rs KernelException exactly.
    pub fn terminate(
        exceptions: &'static [Option<Exception<'static>>],
        stack: &'static [StackPointerBacktrace],
        trace: &'static mut [(usize, usize)],
    ) -> ! {
        let mut out = Packet { n: 0 };
        u32le(&mut out, exceptions.len() as u32);
        for item in exceptions {
            let e = item.as_ref().unwrap();
            u32le(&mut out, e.id);
            string(&mut out, e.message);
            for p in e.param {
                out.extend_from_slice(&p.to_le_bytes());
            }
            string(&mut out, e.file);
            u32le(&mut out, e.line);
            u32le(&mut out, e.column);
            string(&mut out, e.function);
        }
        for sp in stack {
            u32le(&mut out, sp.stack_pointer as u32);
            u32le(&mut out, sp.initial_backtrace_size as u32);
            u32le(&mut out, sp.current_backtrace_size as u32);
        }
        u32le(&mut out, trace.len() as u32);
        for &(ip, sp) in trace.iter() {
            u32le(&mut out, ip as u32);
            u32le(&mut out, sp as u32);
        }
        out.push(unsafe { crate::worker_async_errors() } as u8);
        crate::publish_from_body(8, out.n);
        if crate::command() != 6 {
            crate::fail(b"exception acknowledgement missing");
        }
        // No destructors are skipped in a continuing Rust activation: we discard
        // the CPU1 worker activation and rebuild its private heaps at the entry.
        unsafe {
            crate::worker_rtio_init();
            crate::worker_recover()
        }
    }
}
