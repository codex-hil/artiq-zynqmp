// SPDX-License-Identifier: LGPL-3.0-or-later
use protocol::Packet;
use master_leaf_codec::aux_master_star_path_encode;
extern "C" {fn master_star_wire_test(destination:u32,expected:*const u8,n:usize)->i32;}
pub fn run(){
 // Construct the exact pinned upstream default_master(1) algorithm rather than
 // reusing the new encoder's branch construction as its expected oracle.
 let mut table=[[0xffu8;32];256];
 for i in 0..2 {table[i][0]=i as u8;}
 for i in 1..2 {table[i][1]=0;}
 for destination in 0usize..256 {
  let packet=Packet::RoutingSetPath{destination:destination as u8,hops:table[destination]};
  let expected=super::encode(&packet);let mut bytes=[0xa5u8;1024];
  assert_eq!(unsafe{aux_master_star_path_encode(destination as u32,bytes.as_mut_ptr(),1024)},40);
  assert_eq!(&bytes[..40],&expected[..]);assert_eq!(super::decode(&bytes[..40]).unwrap(),packet);
  assert!(bytes[40..].iter().all(|x|*x==0xa5));
  assert_eq!(unsafe{master_star_wire_test(destination as u32,expected.as_ptr(),expected.len())},0);
 }
 // Master rank0: local0, remote1; satellite rank1: dest0 upstream, dest1 local.
 assert_eq!(table[0][0],0);assert_eq!(table[1][0],1);
 assert_eq!(table[0][1],0xff);assert_eq!(table[1][1],0);
 assert!(table[2..].iter().all(|h|h.iter().all(|x|*x==0xff)));
 for destination in [256u32,u32::MAX].iter(){let mut b=[0xa5u8;40];assert_eq!(unsafe{aux_master_star_path_encode(*destination,b.as_mut_ptr(),40)},-2);assert!(b.iter().all(|x|*x==0xa5));}
 for capacity in [0usize,39,1025,usize::MAX].iter(){let mut b=[0xa5u8;40];assert_eq!(unsafe{aux_master_star_path_encode(1,b.as_mut_ptr(),*capacity)},-4);assert!(b.iter().all(|x|*x==0xa5));}
 assert_eq!(unsafe{aux_master_star_path_encode(1,core::ptr::null_mut(),40)},-4);
 println!("TEST MASTER_STAR_TABLE PASS entries=256");
}
