// SPDX-License-Identifier: LGPL-3.0-or-later
// Checked basic master candidate; host/isolated target only, not firmware service.
use core::slice;
use io::{Cursor,ProtoWrite};
use protocol::Packet;
#[no_mangle]
pub unsafe extern "C" fn aux_master_control_encode(kind:u32,value:u32,buffer:*mut u8,capacity:usize)->i32 {
 if buffer.is_null()||capacity<8||capacity>1024{return -4;}
 let packet=match(kind,value){
  (0,0)=>Packet::EchoRequest,
  (0x20,1)=>Packet::DestinationStatusRequest{destination:1},
  _=>return -2,
 };
 let mut writer=Cursor::new(slice::from_raw_parts_mut(buffer,capacity));
 if packet.write_to(&mut writer).is_err(){return -3;}
 let padding=(12-writer.position()%8)%8;
 for _ in 0..padding{if writer.write_u8(0).is_err(){return -3;}}
 let sum=crc::crc32::checksum_ieee(&writer.get_ref()[..writer.position()]);
 if writer.write_u32(sum).is_err(){return -3;}
 writer.position() as i32
}
// Exact fixed replies only. TSC ACK is received; never encoded as a time-set.
#[no_mangle]
pub unsafe extern "C" fn aux_master_control_decode(buffer:*const u8,length:usize)->i32 {
 if buffer.is_null()||length!=8{return -4;}
 let b=slice::from_raw_parts(buffer,length);
 let expected=crc::crc32::checksum_ieee(&b[..4]);
 let actual=(b[4] as u32)|((b[5] as u32)<<8)|((b[6] as u32)<<16)|((b[7] as u32)<<24);
 if expected!=actual{return -1;}
 match b[0]{1|4|0x21|0x22=>(),_=>return -2};
 let mut reader=Cursor::new(b);
 match Packet::read_from(&mut reader){
  Ok(Packet::EchoReply)=>1,Ok(Packet::TSCAck)=>4,
  Ok(Packet::DestinationDownReply)=>0x21,Ok(Packet::DestinationOkReply)=>0x22,
  _=>-3,
 }
}
