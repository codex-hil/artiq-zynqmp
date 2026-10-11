// Host reference vectors using the actual upstream ARTIQ codec.
// LGPL-3.0-or-later; upstream source retains its own notices.
#[macro_use]
extern crate failure_derive;
extern crate core;
extern crate failure;
extern crate io;
extern crate crc;
use io::{Cursor, ProtoWrite, ProtoRead};
mod protocol { include!(env!("ARTIQ_AUX_PROTOCOL")); }
use protocol::Packet;

fn encode(packet: &Packet) -> Vec<u8> {
    let mut storage = [0u8; 1024];
    let length;
    {
        let mut cursor = Cursor::new(&mut storage[..]);
        packet.write_to(&mut cursor).unwrap();
        let padding = (12 - cursor.position() % 8) % 8;
        for _ in 0..padding { cursor.write_u8(0).unwrap(); }
        let checksum = crc::crc32::checksum_ieee(&cursor.get_ref()[..cursor.position()]);
        cursor.write_u32(checksum).unwrap();
        length = cursor.position();
    }
    storage[..length].to_vec()
}

fn decode(buffer: &[u8]) -> Result<Packet, &'static str> {
    let mut cursor = Cursor::new(buffer);
    let packet = Packet::read_from(&mut cursor).map_err(|_| "protocol")?;
    let padding = (12 - cursor.position() % 8) % 8;
    let checksum_at = cursor.position() + padding;
    if checksum_at + 4 > buffer.len() { return Err("short"); }
    let expected = crc::crc32::checksum_ieee(&buffer[..checksum_at]);
    cursor.set_position(checksum_at);
    if cursor.read_u32().map_err(|_| "short")? != expected { return Err("crc"); }
    Ok(packet)
}

fn main() {
    let cases = [("echo_request", Packet::EchoRequest),
                 ("echo_reply", Packet::EchoReply),
                 ("reset_request", Packet::ResetRequest),
                 ("reset_ack", Packet::ResetAck),
                 ("destination_request", Packet::DestinationStatusRequest { destination: 1 }),
                 ("destination_down", Packet::DestinationDownReply),
                 ("destination_ok", Packet::DestinationOkReply)];
    for (name, packet) in cases.iter() {
        let bytes = encode(packet);
        assert_eq!(decode(&bytes).unwrap(), *packet);
        let mut corrupt = bytes.clone();
        corrupt[bytes.len()-1] ^= 1;
        assert_eq!(decode(&corrupt).unwrap_err(), "crc");
        assert!(decode(&bytes[..bytes.len()-1]).is_err());
        print!("VECTOR {} ", name);
        for byte in bytes { print!("{:02x}",byte); }
        println!();
    }
    assert!(decode(&[0xff;8]).is_err());
    println!("TEST UPSTREAM_AUX_CODEC PASS");
}
