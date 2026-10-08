//! Local ZynqMP adapters for M-Labs CoreDMA ABI and record encoding.
//! Original implementations preserved in ../upstream-dma (LGPL-3.0).
//! Fixed DDR slots replace Zynq mutex/BTreeMap/cache ownership: CPU1 alone
//! owns this region, with MMU/cache off, across kernel loads and recovery.
use crate::{artiq_raise, now_mu};
use core::ptr;
use cslice::CSlice;
const BASE: usize = 0x22000000;
const SLOTS: usize = 32;
const SLOT_BYTES: usize = 65536;
const NAME_BYTES: usize = 64;
const ALIGNMENT: usize = 128;
#[derive(Clone, Copy)]
struct Trace {
    name: [u8; NAME_BYTES],
    name_len: usize,
    valid: bool,
    duration: i64,
    used: usize,
}
const EMPTY: Trace = Trace {
    name: [0; NAME_BYTES],
    name_len: 0,
    valid: false,
    duration: 0,
    used: 0,
};
static mut STORE: [Trace; SLOTS] = [EMPTY; SLOTS];
static mut RECORDER: Option<usize> = None;
#[repr(C)]
pub struct DmaTrace {
    // NAC3 322b7bd tuple ABI: ObjectHeader, then scalar tuple fields.
    // These primitive-only tuples have no refcounted children.
    refcount: u32,
    typeinfo_offset: i32,
    duration: i64,
    address: i32,
    uses_ddma: bool,
}
const _: () = {
    assert!(core::mem::size_of::<DmaTrace>() == 24);
    assert!(core::mem::offset_of!(DmaTrace, duration) == 8);
    assert!(core::mem::offset_of!(DmaTrace, address) == 16);
    assert!(core::mem::offset_of!(DmaTrace, uses_ddma) == 20);
};
extern "C" {
    fn worker_dma_playback(
        timestamp: i64,
        address: u32,
        channel: *mut u32,
        error_timestamp: *mut i64,
    ) -> u32;
}
fn checked_name<'a>(name: CSlice<'a, u8>) -> &'a [u8] {
    if name.len() > NAME_BYTES {
        artiq_raise!("DMAError", "DMA trace name exceeds 64 bytes");
    }
    if name.len() == 0 {
        return &[];
    }
    // Valid only inside the syscall; never saved as a borrowed kernel pointer.
    unsafe { core::slice::from_raw_parts(name.as_ptr(), name.len()) }
}
unsafe fn find(name: &[u8]) -> Option<usize> {
    for i in 0..SLOTS {
        if STORE[i].valid && &STORE[i].name[..STORE[i].name_len] == name {
            return Some(i);
        }
    }
    None
}
pub fn abort_recording() {
    unsafe {
        if let Some(i) = RECORDER.take() {
            STORE[i] = EMPTY;
        }
    }
}
pub fn is_recording() -> bool {
    unsafe { RECORDER.is_some() }
}
pub extern "C" fn dma_record_start(name: CSlice<u8>) {
    if is_recording() {
        artiq_raise!("DMAError", "DMA is already recording");
    }
    let name = checked_name(name);
    unsafe {
        let index = find(name).or_else(|| (0..SLOTS).find(|&i| !STORE[i].valid));
        let i = match index {
            Some(i) => i,
            None => {
                artiq_raise!("DMAError", "DMA trace store is full");
            }
        };
        STORE[i] = EMPTY;
        // Name copy must also tolerate unaligned kernel string addresses.
        for j in 0..name.len() {
            STORE[i].name[j] = ptr::read_volatile(name.as_ptr().add(j));
        }
        STORE[i].name_len = name.len();
        RECORDER = Some(i);
    }
}
pub extern "C" fn dma_record_stop(duration: i64, enable_ddma: bool) {
    if enable_ddma {
        abort_recording();
        artiq_raise!(
            "DMAError",
            "Distributed DMA is not supported on this target"
        );
    }
    unsafe {
        let i = match RECORDER.take() {
            Some(i) => i,
            None => {
                artiq_raise!("DMAError", "DMA is not recording");
            }
        };
        // Upstream termination/padding contract: zero marker and up to127
        // padding bytes. Each slot already has the 128-byte AXI alignment.
        let end = STORE[i].used;
        for j in end..end + ALIGNMENT {
            ptr::write_volatile((BASE + i * SLOT_BYTES + j) as *mut u8, 0);
        }
        core::arch::asm!("dsb sy", options(nostack));
        STORE[i].duration = duration;
        STORE[i].valid = true;
    }
}
/// Same scalar record layout as M-Labs dma_record_output_prepare/output:
/// length1 + channel3 + timestamp8 + address1 + data4, all fields LE.
pub fn record_output(target: i32, word: i32) {
    let timestamp = now_mu();
    unsafe {
        let i = RECORDER.unwrap();
        const LENGTH: usize = 17;
        let offset = STORE[i].used;
        if offset + LENGTH + ALIGNMENT > SLOT_BYTES {
            abort_recording();
            artiq_raise!("DMAError", "DMA trace exceeds slot capacity");
        }
        let header = [
            LENGTH as u8,
            (target >> 8) as u8,
            (target >> 16) as u8,
            (target >> 24) as u8,
            timestamp as u8,
            (timestamp >> 8) as u8,
            (timestamp >> 16) as u8,
            (timestamp >> 24) as u8,
            (timestamp >> 32) as u8,
            (timestamp >> 40) as u8,
            (timestamp >> 48) as u8,
            (timestamp >> 56) as u8,
            target as u8,
            word as u8,
            (word >> 8) as u8,
            (word >> 16) as u8,
            (word >> 24) as u8,
        ];
        for (j, &v) in header.iter().enumerate() {
            ptr::write_volatile((BASE + i * SLOT_BYTES + offset + j) as *mut u8, v);
        }
        STORE[i].used += LENGTH;
    }
}
pub extern "C" fn dma_erase(name: CSlice<u8>) {
    if is_recording() {
        artiq_raise!("DMAError", "Cannot erase while DMA is recording");
    }
    let name = checked_name(name);
    unsafe {
        if let Some(i) = find(name) {
            STORE[i] = EMPTY;
        }
    }
}
pub extern "C" fn dma_retrieve(name: CSlice<u8>) -> DmaTrace {
    let name = checked_name(name);
    unsafe {
        if let Some(i) = find(name) {
            return DmaTrace {
                refcount: 0,
                typeinfo_offset: 0,
                duration: STORE[i].duration,
                address: (BASE + i * SLOT_BYTES) as i32,
                uses_ddma: false,
            };
        }
    }
    artiq_raise!("DMAError", "DMA trace not found");
}
pub extern "C" fn dma_playback(timestamp: i64, address: i32, uses_ddma: bool) {
    if uses_ddma || is_recording() {
        artiq_raise!("DMAError", "Invalid DMA playback state");
    }
    let address = address as u32 as usize;
    if address < BASE || address >= BASE + SLOTS * SLOT_BYTES || (address - BASE) % SLOT_BYTES != 0
    {
        artiq_raise!("DMAError", "Invalid DMA trace pointer");
    }
    unsafe {
        if !STORE[(address - BASE) / SLOT_BYTES].valid {
            artiq_raise!("DMAError", "DMA trace has been erased");
        }
    }
    let mut channel = 0;
    let mut error_timestamp = 0;
    let error = unsafe {
        worker_dma_playback(
            timestamp,
            address as u32,
            &mut channel,
            &mut error_timestamp,
        )
    };
    match error {
        0 => (),
        1 => {
            artiq_raise!(
                "RTIOUnderflow",
                "RTIO DMA underflow at {1} mu, channel {0}",
                channel as i64,
                error_timestamp,
                0
            );
        }
        2 => {
            artiq_raise!(
                "RTIODestinationUnreachable",
                "RTIO DMA destination unreachable at {1} mu, channel {0}",
                channel as i64,
                error_timestamp,
                0
            );
        }
        4 => {
            artiq_raise!("DMAError", "AXI read error during DMA playback");
        }
        8 => {
            artiq_raise!("DMAError", "This bitstream does not support RTIO DMA");
        }
        _ => crate::fail(b"DMA hardware timeout; full runtime restart required"),
    }
}
