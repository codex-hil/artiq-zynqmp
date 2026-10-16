//! Minimal C ABI around the unchanged upstream AUX packet codec.
//! LGPL-3.0-or-later; upstream modules retain their own notices.
#![no_std]
#[macro_use]
extern crate failure_derive;
extern crate failure;
extern crate io;
extern crate crc;
use io::{Cursor, ProtoRead, ProtoWrite};
use core::slice;
mod protocol { include!(env!("ARTIQ_AUX_PROTOCOL")); }
use protocol::Packet;
extern "C" { fn aux_panic() -> !; }
#[panic_handler]
fn panic(_: &core::panic::PanicInfo) -> ! { unsafe { aux_panic() } }

#[no_mangle]
pub unsafe extern "C" fn aux_encode(kind: u32, destination: u32, buffer: *mut u8, capacity: usize) -> i32 {
    if buffer.is_null() || capacity > 1024 || capacity < 8 { return -4; }
    let packet = match kind {
        0 => Packet::EchoRequest, 1 => Packet::EchoReply,
        2 => Packet::ResetRequest, 3 => Packet::ResetAck, 4 => Packet::TSCAck,
        0x20 => Packet::DestinationStatusRequest { destination: destination as u8 },
        0x21 => Packet::DestinationDownReply,
        0x22 => Packet::DestinationOkReply,
        0x32 => Packet::RoutingAck,
        _ => return -2,
    };
    let bytes = slice::from_raw_parts_mut(buffer, capacity);
    let mut writer = Cursor::new(bytes);
    if packet.write_to(&mut writer).is_err() { return -3; }
    let padding = (12 - writer.position() % 8) % 8;
    for _ in 0..padding { if writer.write_u8(0).is_err() { return -3; } }
    let checksum = crc::crc32::checksum_ieee(&writer.get_ref()[..writer.position()]);
    if writer.write_u32(checksum).is_err() { return -3; }
    writer.position() as i32
}

#[no_mangle]
pub unsafe extern "C" fn aux_decode(buffer: *const u8, length: usize, destination: *mut u32) -> i32 {
    if buffer.is_null() || destination.is_null() || length > 1024 { return -4; }
    let bytes = slice::from_raw_parts(buffer, length);
    // DDMA must use the checked full-field ABI, never the legacy scalar path.
    if bytes.first().map_or(false, |b| *b >= 0xb0 && *b <= 0xb6) { return -2; }
    let mut reader = Cursor::new(bytes);
    let packet = match Packet::read_from(&mut reader) { Ok(packet) => packet, Err(_) => return -2 };
    let checksum_at = reader.position() + (12 - reader.position() % 8) % 8;
    if checksum_at + 4 > length { return -3; }
    let expected = crc::crc32::checksum_ieee(&bytes[..checksum_at]);
    reader.set_position(checksum_at);
    match reader.read_u32() { Ok(checksum) if checksum == expected => (), _ => return -1 };
    *destination = 0;
    match packet {
        Packet::EchoRequest => 0, Packet::EchoReply => 1,
        Packet::ResetRequest => 2, Packet::ResetAck => 3, Packet::TSCAck => 4,
        Packet::DestinationStatusRequest { destination: d } => { *destination = d as u32; 0x20 },
        Packet::DestinationDownReply => 0x21,
        Packet::DestinationOkReply => 0x22,
        Packet::RoutingAck => 0x32,
        // Explicit single-hop leaf: master port1, rank1, no repeater.
        // Return destination plus the reviewed local-hop predicate to C.
        Packet::RoutingSetPath { destination: d, hops } => {
            *destination = d as u32 | (((hops[0] == 1 && hops[1] == 0) as u32) << 8);
            0x30
        },
        Packet::RoutingSetRank { rank } => { *destination=rank as u32; 0x31 },
        _ => -2,
    }
}

#[no_mangle]
pub unsafe extern "C" fn aux_crc(buffer: *const u8, length: usize) -> u32 {
    if buffer.is_null() || length > 1024 { return 0; }
    crc::crc32::checksum_ieee(slice::from_raw_parts(buffer,length))
}

mod ddma_codec;
