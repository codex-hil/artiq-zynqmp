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

extern "C" { fn ddma_wire_test() -> i32; }
fn main() {
    assert_eq!(unsafe { ddma_wire_test() },0);
    println!("TEST DDMA_WIRE_SERVICE PASS");
    test_ddma_abi();
    test_master_leaf_abi();
    test_master_leaf_bounds::run();
    test_master_control_codec::run();
    test_master_setup_composition();
    test_master_full_setup_composition();
    test_master_star_table::run();
    assert_eq!(unsafe{master_star_setup_test()},0);
    println!("TEST MASTER_STAR_SETUP PASS");
    assert_eq!(unsafe{master_star_step_test()},0);
    println!("TEST MASTER_STAR_STEP PASS");
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

mod master_leaf_codec;
extern "C" {fn master_leaf_wire_test()->i32;fn master_route_setup_test()->i32;fn master_route_wire_test(ack:*const u8,length:usize)->i32;fn master_ack_slot_test(ack:*const u8,length:usize)->i32;fn master_route_queue_test(ack:*const u8,length:usize)->i32;fn master_mmio_route_test(ack:*const u8,length:usize)->i32;}
fn test_master_leaf_abi() {
    assert_eq!(unsafe{master_leaf_wire_test()},0);
    assert_eq!(unsafe{master_route_setup_test()},0);
    println!("TEST MASTER_ROUTE_SETUP_MOCK PASS");
    let ack=encode(&Packet::RoutingAck);
    assert_eq!(ack,vec![0x32,0,0,0,0x36,0xef,0x66,0x7b]); // QEMU harness golden fixture
    assert_eq!(unsafe{master_route_wire_test(ack.as_ptr(),ack.len())},0);
    assert_eq!(unsafe{master_ack_slot_test(ack.as_ptr(),ack.len())},0);
    println!("TEST MASTER_ACK_SLOT PASS");
    assert_eq!(unsafe{master_route_queue_test(ack.as_ptr(),ack.len())},0);
    println!("TEST MASTER_ROUTE_QUEUE PASS");
    assert_eq!(unsafe{master_cooperative_transport_test(ack.as_ptr(),ack.len())},0);
    println!("TEST MASTER_COOPERATIVE_TRANSPORT PASS");
    assert_eq!(unsafe{master_mmio_route_test(ack.as_ptr(),ack.len())},0);
    println!("TEST MASTER_FULL_MMIO_ROUTE PASS");
    use master_leaf_codec::aux_master_routing_ack_decode;
    assert_eq!(unsafe{aux_master_routing_ack_decode(core::ptr::null(),8)},-4);
    for n in 0..8 {assert_eq!(unsafe{aux_master_routing_ack_decode(ack.as_ptr(),n)},-4);}
    for bit in 0..64 {
        let mut corrupt=ack.clone();corrupt[bit/8]^=1<<(bit%8);
        assert_eq!(unsafe{aux_master_routing_ack_decode(corrupt.as_ptr(),8)},-1);
    }
    let echo=encode(&Packet::EchoReply);
    assert_eq!(unsafe{aux_master_routing_ack_decode(echo.as_ptr(),echo.len())},-2);
    println!("TEST MASTER_ROUTE_WIRE PASS DUPLICATE_ACK_UNCORRELATED");
    use master_leaf_codec::aux_master_leaf_encode;
    let mut hops=[0u8;32];hops[0]=1;
    for (kind,packet,required) in [(0x30,Packet::RoutingSetPath{destination:1,hops:hops},40usize),(0x31,Packet::RoutingSetRank{rank:1},8usize)].iter() {
        for capacity in [*required,1024usize].iter() {
            let mut bytes=[0xa5u8;1024];
            let n=unsafe{aux_master_leaf_encode(*kind,1,bytes.as_mut_ptr(),*capacity)};
            assert_eq!(n,*required as i32);
            assert_eq!(&bytes[..n as usize],&encode(packet)[..]);
            assert_eq!(decode(&bytes[..n as usize]).unwrap(),*packet);
            assert!(bytes[n as usize..].iter().all(|x| *x==0xa5));
        }
        for capacity in [0usize,*required-1,1025usize].iter() {
            let mut bytes=[0xa5u8;1024];
            assert_eq!(unsafe{aux_master_leaf_encode(*kind,1,bytes.as_mut_ptr(),*capacity)},-4);
            assert!(bytes.iter().all(|x| *x==0xa5));
        }
        for value in [0u32,2,255,256,u32::MAX].iter() {
            let mut bytes=[0xa5u8;1024];
            assert_eq!(unsafe{aux_master_leaf_encode(*kind,*value,bytes.as_mut_ptr(),1024)},-2);
            assert!(bytes.iter().all(|x| *x==0xa5));
        }
    }
    assert_eq!(unsafe{aux_master_leaf_encode(0x30,1,core::ptr::null_mut(),40)},-4);
    let mut bytes=[0xa5u8;1024];
    assert_eq!(unsafe{aux_master_leaf_encode(0x32,1,bytes.as_mut_ptr(),1024)},-2);
    assert!(bytes.iter().all(|x| *x==0xa5));
    println!("TEST MASTER_LEAF_C_ABI PASS");
}

mod test_master_leaf_bounds;

mod master_control_codec;
mod test_master_control_codec;

extern "C" {fn master_setup_composition_test(frames:*const u8,length:usize)->i32;}
fn test_master_setup_composition(){
 let mut frames=Vec::new();
 for packet in [Packet::EchoReply,Packet::TSCAck,Packet::RoutingAck,Packet::DestinationOkReply,Packet::DestinationDownReply].iter(){frames.extend(encode(packet));}
 assert_eq!(unsafe{master_setup_composition_test(frames.as_ptr(),frames.len())},0);
 println!("TEST MASTER_SETUP_COMPOSITION PASS");
}

mod test_master_star_table;

extern "C" {fn master_star_setup_test()->i32;}

extern "C" {fn master_full_setup_composition_test(frames:*const u8,length:usize)->i32;}
fn test_master_full_setup_composition(){
 let mut frames=Vec::new();
 for packet in [Packet::EchoReply,Packet::TSCAck,Packet::RoutingAck,Packet::DestinationOkReply,Packet::DestinationDownReply].iter(){frames.extend(encode(packet));}
 assert_eq!(frames,vec![0x1,0x0,0x0,0x0,0x79,0xb8,0xf8,0x99,0x4,0x0,0x0,0x0,0x4b,0x48,0x26,0xae,0x32,0x0,0x0,0x0,0x36,0xef,0x66,0x7b,0x22,0x0,0x0,0x0,0xa9,0xb8,0x7f,0x2b,0x21,0x0,0x0,0x0,0x47,0x17,0xca,0x39]); // Emulator fixed-reply fixture equals upstream
 assert_eq!(unsafe{master_full_setup_composition_test(frames.as_ptr(),frames.len())},0);
 println!("TEST MASTER_FULL_SETUP_COMPOSITION PASS");
}

extern "C" {fn master_star_step_test()->i32;}

extern "C" {fn master_cooperative_transport_test(ack:*const u8,n:usize)->i32;}
