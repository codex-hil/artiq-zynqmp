// SPDX-License-Identifier: LGPL-3.0-or-later
//! Fixed encoder byte equivalence against unchanged upstream serialization.
use protocol::Packet;
use master_leaf_codec::{aux_master_leaf_encode,aux_master_star_path_encode};
use master_control_codec::aux_master_control_encode;
pub fn run(){
 let mut calls=0;
 for destination in 0u32..256 {
  let mut hops=[0xffu8;32];
  if destination==0 {hops[0]=0;}
  if destination==1 {hops[0]=1;hops[1]=0;}
  let expected=super::encode(&Packet::RoutingSetPath{destination:destination as u8,hops:hops});
  for capacity in 0usize..=1025 {
   let mut b=[0xa5u8;1026];
   let result=unsafe{aux_master_star_path_encode(destination,b.as_mut_ptr(),capacity)};
   if capacity>=40 && capacity<=1024 {assert_eq!(result,40);assert_eq!(&b[..40],&expected[..]);assert!(b[40..].iter().all(|x|*x==0xa5));}
   else {assert_eq!(result,-4);assert!(b.iter().all(|x|*x==0xa5));}
   calls+=1;
  }
 }
 let mut hops=[0u8;32];hops[0]=1;
 for (kind,value,packet,control) in vec![(0x30,1,Packet::RoutingSetPath{destination:1,hops:hops},false),(0x31,1,Packet::RoutingSetRank{rank:1},false),(0,0,Packet::EchoRequest,true),(0x20,1,Packet::DestinationStatusRequest{destination:1},true)] {
  let expected=super::encode(&packet);
  for capacity in 0usize..=1025 {
   let mut b=[0x5au8;1026];
   let result=unsafe{if control{aux_master_control_encode(kind,value,b.as_mut_ptr(),capacity)}else{aux_master_leaf_encode(kind,value,b.as_mut_ptr(),capacity)}};
   if capacity>=expected.len() && capacity<=1024 {assert_eq!(result,expected.len() as i32);assert_eq!(&b[..expected.len()],&expected[..]);assert!(b[expected.len()..].iter().all(|x|*x==0x5a));}
   else {assert_eq!(result,-4);assert!(b.iter().all(|x|*x==0x5a));}
   calls+=1;
  }
 }
 println!("TEST MASTER_ENCODE_ORACLE PASS calls={}",calls);
}
