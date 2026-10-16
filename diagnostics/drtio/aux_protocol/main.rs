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
    test_ddma_abi();
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

mod ddma_codec;

fn test_ddma_abi() {
    use ddma_codec::{DdmaPacket,aux_ddma_encode,aux_ddma_decode};
    assert_eq!(core::mem::size_of::<DdmaPacket>(),1056);
    assert_eq!(core::mem::offset_of!(DdmaPacket,timestamp),32);
    assert_eq!(core::mem::offset_of!(DdmaPacket,trace),40);
    let mut d=DdmaPacket {source:0,destination:1,id:0xfedcba98,status:3,length:17,succeeded:1,error:7,channel:0x123456,timestamp:0x123456789abcdef,trace:[0;protocol::MASTER_PAYLOAD_MAX_SIZE]};
    d.trace[..17].copy_from_slice(&[17,0,0,1,8,0,0,0,0,0,0,0,0,1,0,0,0]);
    for kind in 0xb0..=0xb6 {
        let mut bytes=[0u8;1024];let mut out=d.clone();
        let n=unsafe {aux_ddma_encode(kind,&d,bytes.as_mut_ptr(),bytes.len())};assert!(n>0);
        let reference=decode(&bytes[..n as usize]).unwrap();
        assert_eq!(encode(&reference),bytes[..n as usize]);
        assert_eq!(unsafe{aux_ddma_decode(bytes.as_ptr(),n as usize,&mut out)},kind as i32);
        assert_eq!(out.destination,1);
        if kind==0xb0 || kind==0xb1 || kind==0xb2 || kind==0xb4 || kind==0xb6 {assert_eq!(out.id,d.id);assert_eq!(out.source,d.source);}
        if kind==0xb1 || kind==0xb3 || kind==0xb5 {assert_eq!(out.succeeded,1);}
        if kind==0xb0 {assert_eq!(out.length,17);assert_eq!(&out.trace[..17],&d.trace[..17]);assert_eq!(out.status,3);}
        if kind==0xb4 || kind==0xb6 {assert_eq!(out.timestamp,d.timestamp);}
        if kind==0xb6 {assert_eq!(out.error,7);assert_eq!(out.channel,d.channel);}
        for len in 0..n as usize {assert!(unsafe{aux_ddma_decode(bytes.as_ptr(),len,&mut out)}<0);}
        bytes[n as usize-1]^=1;
        assert_eq!(unsafe{aux_ddma_decode(bytes.as_ptr(),n as usize,&mut out)},-1);
    }
    let mut bytes=[0u8;1024];let mut out=d.clone();
    let n=unsafe{aux_ddma_encode(0xb0,&d,bytes.as_mut_ptr(),1024)} as usize;
    bytes[7]=4;assert!(unsafe{aux_ddma_decode(bytes.as_ptr(),n,&mut out)}<0);
    bytes[7]=3;bytes[8]=255;bytes[9]=255;
    assert!(unsafe{aux_ddma_decode(bytes.as_ptr(),n,&mut out)}<0);
    d.length=protocol::MASTER_PAYLOAD_MAX_SIZE as u32;
    let n=unsafe{aux_ddma_encode(0xb0,&d,bytes.as_mut_ptr(),1024)};
    assert_eq!(n,1024);assert_eq!(unsafe{aux_ddma_decode(bytes.as_ptr(),1024,&mut out)},0xb0);
    d.length+=1;assert!(unsafe{aux_ddma_encode(0xb0,&d,bytes.as_mut_ptr(),1024)}<0);
    println!("TEST DDMA_C_ABI PASS");
}
