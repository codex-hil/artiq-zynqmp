// SPDX-License-Identifier: LGPL-3.0-or-later
use master_control_codec::{aux_master_control_encode,aux_master_control_decode};
use protocol::Packet;
extern "C" {fn master_control_wire_test(packet:*const u8,n:usize,kind:u32)->i32;}
pub fn run(){
 let mut calls=0u32;
 for (kind,value,packet) in [(0,0,Packet::EchoRequest),(0x20,1,Packet::DestinationStatusRequest{destination:1})].iter(){
  let expected=super::encode(packet);
  for cap in 0usize..=1025{
   let mut b=[0xa5u8;1026];let n=unsafe{aux_master_control_encode(*kind,*value,b.as_mut_ptr(),cap)};calls+=1;
   if cap<8||cap>1024{assert_eq!(n,-4);assert!(b.iter().all(|x|*x==0xa5));}
   else{assert_eq!(n,8);assert_eq!(&b[..8],&expected[..]);assert!(b[8..].iter().all(|x|*x==0xa5));}
  }
 }
 for (kind,packet) in [(1,Packet::EchoReply),(4,Packet::TSCAck),(0x21,Packet::DestinationDownReply),(0x22,Packet::DestinationOkReply)].iter(){
  let b=super::encode(packet);assert_eq!(unsafe{aux_master_control_decode(b.as_ptr(),b.len())},*kind as i32);calls+=1;
  assert_eq!(unsafe{master_control_wire_test(b.as_ptr(),b.len(),*kind)},0);
  for bit in 0..64{let mut bad=b.clone();bad[bit/8]^=1<<(bit%8);assert_eq!(unsafe{aux_master_control_decode(bad.as_ptr(),8)},-1);calls+=1;}
  for n in [0usize,7,9,1024,usize::MAX].iter(){assert_eq!(unsafe{aux_master_control_decode(b.as_ptr(),*n)},-4);calls+=1;}
 }
 for kind in 0u32..256{
  let mut b=[0u8;8];b[0]=kind as u8;let sum=crc::crc32::checksum_ieee(&b[..4]);for i in 0..4{b[4+i]=(sum>>(i*8)) as u8;}
  assert_eq!(unsafe{aux_master_control_decode(b.as_ptr(),8)},if [1,4,0x21,0x22].contains(&kind){kind as i32}else{-2});calls+=1;
 }
 for (kind,value) in [(0,1),(0x20,0),(0x20,256),(4,0),(3,0),(0x30,1),(u32::MAX,u32::MAX)].iter(){
  let mut b=[0xa5u8;16];assert_eq!(unsafe{aux_master_control_encode(*kind,*value,b.as_mut_ptr(),16)},-2);assert!(b.iter().all(|x|*x==0xa5));calls+=1;
 }
 assert_eq!(unsafe{aux_master_control_encode(0,0,core::ptr::null_mut(),8)},-4);
 assert_eq!(unsafe{aux_master_control_decode(core::ptr::null(),8)},-4);
 println!("TEST MASTER_CONTROL_CODEC PASS calls={}",calls);
}
