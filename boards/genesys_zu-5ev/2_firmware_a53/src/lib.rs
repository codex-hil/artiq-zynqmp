//! A53 services using Piotr's C BSP -> Rust staticlib architecture.
//! Management wire ABI follows the pinned current ARTIQ CommMgmt client.
//! This is an initial management layer, not the ARTIQ kernel/RPC runtime.
#![no_std]

use core::cell::UnsafeCell;
use core::slice;

const MAGIC: &[u8] = b"ARTIQ management\n";
const LOG_SIZE: usize = 1024;

struct Runtime {
    log: [u8; LOG_SIZE],
    log_len: usize,
    ip: [u8; 16],
    ip_len: usize,
    kernel_ready: bool,
}
impl Runtime {
    const fn new() -> Self {
        Self { log: [0; LOG_SIZE], log_len: 0, ip: [0; 16], ip_len: 0, kernel_ready: false }
    }
    fn append(&mut self, bytes: &[u8]) {
        let bytes = &bytes[bytes.len().saturating_sub(LOG_SIZE)..];
        let excess = (self.log_len + bytes.len()).saturating_sub(LOG_SIZE);
        if excess != 0 {
            self.log.copy_within(excess..self.log_len, 0);
            self.log_len -= excess;
        }
        self.log[self.log_len..self.log_len + bytes.len()].copy_from_slice(bytes);
        self.log_len += bytes.len();
    }
    fn ready(&mut self, ip: &[u8]) {
        self.kernel_ready = false;
        self.ip_len = ip.len().min(self.ip.len());
        self.ip[..self.ip_len].copy_from_slice(&ip[..self.ip_len]);
        self.append(b"Genesys ZU-5EV: Rust management service started over AMD GEM/lwIP.\n");
        self.append(b"Runtime mode: management-only; kernel execution/RPC unavailable.\nDHCP: ");
        self.append(ip);
        self.append(b"\nLocal RTIO: A53 CSR counter access enabled.\n");
    }
}

#[repr(C)]
struct Session {
    mode: u8,
    offset: usize,
    length: [u8; 4],
    key: [u8; 128],
    key_len: usize,
}
impl Session {
    const fn new() -> Self {
        Self { mode: 0, offset: 0, length: [0; 4], key: [0; 128], key_len: 0 }
    }
    fn byte(&mut self, runtime: &mut Runtime, byte: u8, out: &mut [u8]) -> Result<usize, ()> {
        if out.len() < LOG_SIZE + 5 { return Err(()); }
        match self.mode {
            0 => {
                if byte != MAGIC[self.offset] { return Err(()); }
                self.offset += 1;
                if self.offset == MAGIC.len() { self.mode = 1; self.offset = 0; }
                Ok(0)
            }
            1 => {
                if byte != 0 { return Err(()); } // DRTIO destination unsupported.
                self.mode = 2;
                out[0] = b'e'; // AArch64 little-endian management payloads.
                Ok(1)
            }
            2 => match byte {
                1 => {
                    let n = data_reply(2, &runtime.log[..runtime.log_len], out);
                    Ok(n)
                }
                2 => { runtime.log_len = 0; out[0] = 1; Ok(1) }
                12 => { self.mode = 3; self.offset = 0; Ok(0) }
                _ => { self.mode = 5; out[0] = 6; Ok(1) } // Error, then orderly transport close.
            },
            3 => {
                self.length[self.offset] = byte;
                self.offset += 1;
                if self.offset == 4 {
                    self.key_len = u32::from_le_bytes(self.length) as usize;
                    if self.key_len == 0 || self.key_len > self.key.len() { return Err(()); }
                    self.offset = 0;
                    self.mode = 4;
                }
                Ok(0)
            }
            4 => {
                if !byte.is_ascii() { return Err(()); }
                self.key[self.offset] = byte;
                self.offset += 1;
                if self.offset != self.key_len { return Ok(0); }
                self.mode = 2;
                let key = &self.key[..self.key_len];
                runtime.append(b"Management configuration read.\n");
                let value: &[u8] = match key {
                    b"ip" => &runtime.ip[..runtime.ip_len],
                    b"mac" => b"02:38:3b:7f:02:0d",
                    b"board" => b"genesys_zu-5ev",
                    b"runtime_mode" => if runtime.kernel_ready { b"kernel-bringup" } else { b"management-only" },
                    b"rtio_counter" => {
                        if !rtio_available() { out[0] = 6; return Ok(1); }
                        let mut digits = [0u8; 20];
                        let mut value = rtio_counter();
                        let mut start = digits.len();
                        loop {
                            start -= 1;
                            digits[start] = b'0' + (value % 10) as u8;
                            value /= 10;
                            if value == 0 { break; }
                        }
                        return Ok(data_reply(7, &digits[start..], out));
                    }
                    _ => { out[0] = 6; return Ok(1); }
                };
                Ok(data_reply(7, value, out))
            }
            _ => Err(()),
        }
    }
}
fn data_reply(kind: u8, data: &[u8], out: &mut [u8]) -> usize {
    out[0] = kind;
    out[1..5].copy_from_slice(&(data.len() as u32).to_le_bytes());
    out[5..5 + data.len()].copy_from_slice(data);
    5 + data.len()
}

#[cfg(not(test))]
fn rtio_available() -> bool {
    extern "C" { fn genesys_kernel_running() -> i32; }
    unsafe { genesys_kernel_running() == 0 }
}
#[cfg(test)] fn rtio_available() -> bool { true }

#[cfg(not(test))]
fn rtio_counter() -> u64 {
    extern "C" { fn genesys_rtio_counter() -> u64; }
    unsafe { genesys_rtio_counter() }
}
#[cfg(test)]
fn rtio_counter() -> u64 { 123456 } // Explicit unit-test fixture; never hardware evidence.

struct CooperativeRuntime(UnsafeCell<Runtime>);
// C calls this API exclusively in the single-core lwIP foreground context.
// No IRQ callback, other core, reentrant Rust call or task may access it.
unsafe impl Sync for CooperativeRuntime {}
static RUNTIME: CooperativeRuntime = CooperativeRuntime(UnsafeCell::new(Runtime::new()));

#[no_mangle]
pub extern "C" fn artiq_session_size() -> usize { core::mem::size_of::<Session>() }
#[no_mangle]
pub extern "C" fn artiq_session_align() -> usize { core::mem::align_of::<Session>() }

/// Safety: valid aligned Session storage; exclusively owned by one C connection.
#[no_mangle]
pub unsafe extern "C" fn artiq_session_init(session: *mut u8) {
    session.cast::<Session>().write(Session::new());
    (&mut *RUNTIME.0.get()).append(b"Management TCP connection accepted.\n");
}
/// Safety: exclusive foreground context, valid input bytes and initialized session.
/// Safety: valid event bytes, single-core foreground context.
#[no_mangle]
pub unsafe extern "C" fn artiq_runtime_kernel_event(event: *const u8, len: usize) {
    (&mut *RUNTIME.0.get()).append(slice::from_raw_parts(event,len));
}

#[no_mangle]
pub unsafe extern "C" fn artiq_runtime_kernel_ready() {
    let runtime = &mut *RUNTIME.0.get();
    runtime.kernel_ready = true;
    runtime.log_len = 0;
    runtime.append(b"Genesys ZU-5EV: kernel-bringup; real CPU1 load/run and scalar RPC.\nTTL exports disabled; exceptions/unwind and complex RPC returns pending.\n");
}

#[no_mangle]
pub unsafe extern "C" fn artiq_runtime_ready(ip: *const u8, len: usize) {
    (&mut *RUNTIME.0.get()).ready(slice::from_raw_parts(ip, len));
}
/// Safety: exclusive valid session and writable output buffer; input one wire byte.
#[no_mangle]
pub unsafe extern "C" fn artiq_session_byte(session: *mut u8, byte: u8, out: *mut u8, cap: usize) -> i32 {
    let state = &mut *session.cast::<Session>();
    let runtime = &mut *RUNTIME.0.get();
    match state.byte(runtime, byte, slice::from_raw_parts_mut(out, cap)) {
        Ok(n) => n as i32,
        Err(()) => -1,
    }
}
/// Safety: initialized Session storage, used exclusively by its owner.
#[no_mangle]
pub unsafe extern "C" fn artiq_session_closing(session: *const u8) -> i32 {
    ((*session.cast::<Session>()).mode == 5) as i32
}

#[cfg(not(test))]
#[panic_handler]
fn panic(_info: &core::panic::PanicInfo<'_>) -> ! { loop { core::hint::spin_loop(); } }

#[cfg(test)]
mod tests {
    extern crate std;
    use super::*;
    use std::vec::Vec;
    fn feed(session: &mut Session, runtime: &mut Runtime, data: &[u8]) -> Result<Vec<u8>, ()> {
        let mut result = Vec::new();
        for byte in data {
            let mut out = [0u8; 2048];
            let n = session.byte(runtime, *byte, &mut out)?;
            result.extend_from_slice(&out[..n]);
        }
        Ok(result)
    }
    fn open(s: &mut Session, r: &mut Runtime) { assert_eq!(feed(s, r, b"ARTIQ management\n\0").unwrap(), b"e"); }
    #[test] fn fragmented_handshake_and_coalesced_requests() {
        let (mut s, mut r) = (Session::new(), Runtime::new());
        assert!(feed(&mut s, &mut r, b"ARTIQ manage").unwrap().is_empty());
        assert_eq!(feed(&mut s, &mut r, b"ment\n\0\x02\x01").unwrap(), b"e\x01\x02\0\0\0\0");
    }
    #[test] fn actual_log_read_and_clear() {
        let (mut s, mut r) = (Session::new(), Runtime::new()); open(&mut s, &mut r);
        r.append(b"real event\n");
        assert_eq!(&feed(&mut s, &mut r, &[1]).unwrap()[5..], b"real event\n");
        assert_eq!(feed(&mut s, &mut r, &[2]).unwrap(), &[1]);
        assert_eq!(feed(&mut s, &mut r, &[1]).unwrap(), b"\x02\0\0\0\0");
    }
    #[test] fn config_metadata_and_counter_fixture() {
        let (mut s, mut r) = (Session::new(), Runtime::new()); open(&mut s, &mut r);
        r.ready(b"192.168.2.16");
        assert_eq!(&feed(&mut s, &mut r, b"\x0c\x02\0\0\0ip").unwrap()[5..], b"192.168.2.16");
        assert_eq!(&feed(&mut s, &mut r, b"\x0c\x0c\0\0\0rtio_counter").unwrap()[5..], b"123456");
    }
    #[test] fn reject_bad_greeting_destination_length_and_utf8() {
        assert!(feed(&mut Session::new(), &mut Runtime::new(), b"NOT ARTIQ").is_err());
        assert!(feed(&mut Session::new(), &mut Runtime::new(), b"ARTIQ management\n\x01").is_err());
        for bad in [&b"\x0c\xff\xff\xff\x7f"[..], &b"\x0c\x01\0\0\0\xff"[..]] {
            let (mut s, mut r) = (Session::new(), Runtime::new()); open(&mut s, &mut r);
            assert!(feed(&mut s, &mut r, bad).is_err());
        }
    }
    #[test] fn unsupported_operations_fail_instead_of_fake_success() {
        for op in [5, 7, 8, 9, 13, 14, 15, 99] {
            let (mut s, mut r) = (Session::new(), Runtime::new()); open(&mut s, &mut r);
            assert_eq!(feed(&mut s, &mut r, &[op]).unwrap(), &[6]);
            assert_eq!(s.mode, 5);
        }
    }
    #[test] fn sessions_are_independent_and_log_is_bounded() {
        let (mut a, mut b, mut r) = (Session::new(), Session::new(), Runtime::new());
        feed(&mut a, &mut r, b"ARTIQ ").unwrap(); open(&mut b, &mut r);
        assert_eq!(feed(&mut a, &mut r, b"management\n\0").unwrap(), b"e");
        r.append(&[b'x'; 2048]); assert_eq!(r.log_len, LOG_SIZE);
        assert_eq!(feed(&mut b, &mut r, &[1]).unwrap().len(), LOG_SIZE + 5);
    }
}
