// SPDX-License-Identifier: LGPL-3.0-or-later
//! Finite host coverage of exported fixed-leaf ABI; not proof of system panic safety.
use master_leaf_codec::{aux_master_leaf_encode,aux_master_routing_ack_decode};
pub fn run() {
 let mut calls=0u32;
 for kind in [0x30u32,0x31].iter() {
  let required=if *kind==0x30 {40usize}else{8usize};
  for capacity in 0usize..=1025 {
   let mut out=[0xa5u8;1026];
   let n=unsafe{aux_master_leaf_encode(*kind,1,out.as_mut_ptr(),capacity)};calls+=1;
   if capacity<required||capacity>1024 {assert_eq!(n,-4);assert!(out.iter().all(|b|*b==0xa5));}
   else {assert_eq!(n,required as i32);assert!(out[required..].iter().all(|b|*b==0xa5));}
  }
  for value in 0u32..4096 {
   let mut out=[0xa5u8;1024];
   let n=unsafe{aux_master_leaf_encode(*kind,value,out.as_mut_ptr(),1024)};calls+=1;
   if value==1 {assert_eq!(n,required as i32);}else{assert_eq!(n,-2);assert!(out.iter().all(|b|*b==0xa5));}
  }
 }
 // All65536 kind/first-padding-byte combinations, with a VALID computed CRC.
 // This exercises the guard before upstream dispatch to variable-sized variants.
 for kind in 0u32..256 {for padding in 0u32..256 {
  let mut frame=[0u8;8];frame[0]=kind as u8;frame[1]=padding as u8;
  let sum=crc::crc32::checksum_ieee(&frame[..4]);
  for i in 0..4 {frame[4+i]=(sum>>(i*8)) as u8;}
  let n=unsafe{aux_master_routing_ack_decode(frame.as_ptr(),8)};calls+=1;
  assert_eq!(n,if kind==0x32 {0x32}else{-2});
 }}
 let frame=[0u8;1026];
 for length in 0usize..=1025 {
  if length==8 {continue;}
  assert_eq!(unsafe{aux_master_routing_ack_decode(frame.as_ptr(),length)},-4);calls+=1;
 }
 for length in [usize::MAX,1026usize].iter() {
  assert_eq!(unsafe{aux_master_routing_ack_decode(frame.as_ptr(),*length)},-4);calls+=1;
 }
 println!("TEST MASTER_LEAF_BOUNDS PASS calls={} valid_crc_prefixes=65536",calls);
}
