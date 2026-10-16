// Checked C ABI for unchanged upstream DDMA packets; LGPL-3.0-or-later.
use core::slice;
use io::{Cursor, ProtoRead, ProtoWrite};
use protocol::{Packet, PayloadStatus, MASTER_PAYLOAD_MAX_SIZE};
#[repr(C)]
#[derive(Clone)]
pub struct DdmaPacket {
    pub source:u32, pub destination:u32, pub id:u32, pub status:u32,
    pub length:u32, pub succeeded:u32, pub error:u32, pub channel:u32,
    pub timestamp:u64, pub trace:[u8;MASTER_PAYLOAD_MAX_SIZE],
}
#[no_mangle]
pub unsafe extern "C" fn aux_ddma_decode(buffer:*const u8,length:usize,out:*mut DdmaPacket)->i32 {
    if buffer.is_null() || out.is_null() || length<8 || length>1024 {return -4;}
    let bytes=slice::from_raw_parts(buffer,length);
    if bytes[0]<0xb0 || bytes[0]>0xb6 {return -2;}
    // Upstream slices and PayloadStatus::from assume valid bounds. Reject
    // malformed fields before entering that codec, without patching upstream.
    if bytes[0]==0xb0 {
        if length<10 || bytes[7]>3 {return -3;}
        let n=(bytes[8] as usize)|((bytes[9] as usize)<<8);
        if n>MASTER_PAYLOAD_MAX_SIZE {return -3;}
    }
    let mut r=Cursor::new(bytes);
    let packet=match Packet::read_from(&mut r) {Ok(p)=>p,Err(_)=>return -3};
    let at=r.position()+(12-r.position()%8)%8;
    if at+4>length {return -3;}
    let expected=crc::crc32::checksum_ieee(&bytes[..at]);r.set_position(at);
    if r.read_u32().ok()!=Some(expected) {return -1;}
    let mut d=DdmaPacket {source:0,destination:0,id:0,status:0,length:0,succeeded:0,error:0,channel:0,timestamp:0,trace:[0;MASTER_PAYLOAD_MAX_SIZE]};
    match packet {
        Packet::DmaAddTraceRequest{source,destination,id,status,length,trace}=>{d.source=source as u32;d.destination=destination as u32;d.id=id;d.status=status as u32;d.length=length as u32;d.trace=trace;},
        Packet::DmaAddTraceReply{source,destination,id,succeeded}=>{d.source=source as u32;d.destination=destination as u32;d.id=id;d.succeeded=succeeded as u32;},
        Packet::DmaRemoveTraceRequest{source,destination,id}=>{d.source=source as u32;d.destination=destination as u32;d.id=id;},
        Packet::DmaRemoveTraceReply{destination,succeeded}|Packet::DmaPlaybackReply{destination,succeeded}=>{d.destination=destination as u32;d.succeeded=succeeded as u32;},
        Packet::DmaPlaybackRequest{source,destination,id,timestamp}=>{d.source=source as u32;d.destination=destination as u32;d.id=id;d.timestamp=timestamp;},
        Packet::DmaPlaybackStatus{source,destination,id,error,channel,timestamp}=>{d.source=source as u32;d.destination=destination as u32;d.id=id;d.error=error as u32;d.channel=channel;d.timestamp=timestamp;},
        _=>return -2,
    }
    *out=d;bytes[0] as i32
}
#[no_mangle]
pub unsafe extern "C" fn aux_ddma_encode(kind:u32,data:*const DdmaPacket,buffer:*mut u8,capacity:usize)->i32 {
    if data.is_null() || buffer.is_null() || capacity<8 || capacity>1024 {return -4;}
    let d=&*data;
    if d.source>255 || d.destination>255 || d.status>3 || d.length as usize>MASTER_PAYLOAD_MAX_SIZE || d.succeeded>1 || d.error>255 {return -3;}
    let p=match kind {
        0xb0=>Packet::DmaAddTraceRequest{source:d.source as u8,destination:d.destination as u8,id:d.id,status:PayloadStatus::from(d.status as u8),length:d.length as u16,trace:d.trace},
        0xb1=>Packet::DmaAddTraceReply{source:d.source as u8,destination:d.destination as u8,id:d.id,succeeded:d.succeeded!=0},
        0xb2=>Packet::DmaRemoveTraceRequest{source:d.source as u8,destination:d.destination as u8,id:d.id},
        0xb3=>Packet::DmaRemoveTraceReply{destination:d.destination as u8,succeeded:d.succeeded!=0},
        0xb4=>Packet::DmaPlaybackRequest{source:d.source as u8,destination:d.destination as u8,id:d.id,timestamp:d.timestamp},
        0xb5=>Packet::DmaPlaybackReply{destination:d.destination as u8,succeeded:d.succeeded!=0},
        0xb6=>Packet::DmaPlaybackStatus{source:d.source as u8,destination:d.destination as u8,id:d.id,error:d.error as u8,channel:d.channel,timestamp:d.timestamp},
        _=>return -2,
    };
    let mut w=Cursor::new(slice::from_raw_parts_mut(buffer,capacity));
    if p.write_to(&mut w).is_err(){return -3;}
    let padding=(12-w.position()%8)%8;
    for _ in 0..padding {if w.write_u8(0).is_err(){return -3;}}
    let crc=crc::crc32::checksum_ieee(&w.get_ref()[..w.position()]);
    if w.write_u32(crc).is_err(){return -3;}w.position() as i32
}
