// SPDX-License-Identifier: LGPL-3.0-or-later
//! Fixed C ABI equivalence against unchanged upstream Packet reader/envelope.
use protocol::Packet;
use master_leaf_codec::aux_master_routing_ack_decode;
use master_control_codec::aux_master_control_decode;
fn upstream_kind(b:&[u8])->i32 {
 match super::decode(b).unwrap(){
  Packet::EchoReply=>1,Packet::TSCAck=>4,Packet::DestinationDownReply=>0x21,
  Packet::DestinationOkReply=>0x22,Packet::RoutingAck=>0x32,_=>panic!("unexpected oracle type"),
 }
}
fn frame(kind:u8,padding:u32)->[u8;8]{
 let mut b=[0u8;8];b[0]=kind;b[1]=padding as u8;b[2]=(padding>>8) as u8;b[3]=(padding as u8).wrapping_mul(17)^((padding>>8)as u8)^0xa5;
 let sum=crc::crc32::checksum_ieee(&b[..4]);for i in 0..4{b[4+i]=(sum>>(8*i))as u8;}b
}
pub fn run(){
 let mut calls=0u32;let mut frames=0u32;
 for kind in [1u8,4,0x21,0x22,0x32].iter(){
  for padding in 0u32..65536{
   let b=frame(*kind,padding);let unchanged=b;let oracle=upstream_kind(&b);assert_eq!(oracle,*kind as i32);
   assert_eq!(unsafe{aux_master_routing_ack_decode(b.as_ptr(),8)},if oracle==0x32{oracle}else{-2});
   assert_eq!(unsafe{aux_master_control_decode(b.as_ptr(),8)},if oracle==0x32{-2}else{oracle});
   assert_eq!(b,unchanged);calls+=2;frames+=1;
  }
  for bit in 0..64{
   let mut b=frame(*kind,0x5aa5);b[bit/8]^=1<<(bit%8);
   assert_eq!(unsafe{aux_master_routing_ack_decode(b.as_ptr(),8)},-1);
   assert_eq!(unsafe{aux_master_control_decode(b.as_ptr(),8)},-1);calls+=2;
  }
 }
 // Unsupported kinds are rejected before generic variable-payload parsing.
 // For all valid CRC prefixes this preserves original fixed C ABI policy.
 for kind in 0u32..256{
  let b=frame(kind as u8,0xaff0);
  assert_eq!(unsafe{aux_master_routing_ack_decode(b.as_ptr(),8)},if kind==0x32{kind as i32}else{-2});
  assert_eq!(unsafe{aux_master_control_decode(b.as_ptr(),8)},if [1,4,0x21,0x22].contains(&kind){kind as i32}else{-2});calls+=2;
 }
 let b=[0u8;1026];
 for length in 0usize..=1025{if length!=8{
  assert_eq!(unsafe{aux_master_routing_ack_decode(b.as_ptr(),length)},-4);
  assert_eq!(unsafe{aux_master_control_decode(b.as_ptr(),length)},-4);calls+=2;
 }}
 assert_eq!(unsafe{aux_master_routing_ack_decode(b.as_ptr(),usize::MAX)},-4);
 assert_eq!(unsafe{aux_master_control_decode(b.as_ptr(),usize::MAX)},-4);
 assert_eq!(unsafe{aux_master_routing_ack_decode(core::ptr::null(),8)},-4);
 assert_eq!(unsafe{aux_master_control_decode(core::ptr::null(),8)},-4);calls+=4;
 assert_eq!(frames,327680);
 println!("TEST MASTER_FIXED_DECODE_ORACLE PASS upstream_frames={} abi_calls={}",frames,calls);
}
