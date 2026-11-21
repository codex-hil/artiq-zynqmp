// SPDX-License-Identifier: LGPL-3.0-or-later
// Isolated single-leaf master encoder candidate; not linked into firmware.
use core::slice;

// Only destination1 over port1/rank1 is admitted by this candidate contract.
// Invalid arguments leave output untouched; caller supplies a valid writable buffer.
#[no_mangle]
pub unsafe extern "C" fn aux_master_leaf_encode(kind:u32,value:u32,buffer:*mut u8,capacity:usize)->i32 {
    if buffer.is_null() || capacity>1024 {return -4;}
    let required=match (kind,value) {(0x30,1)=>40,(0x31,1)=>8,_=>return -2};
    if capacity<required {return -4;}
    let bytes=slice::from_raw_parts_mut(buffer,required);
    bytes.fill(0);bytes[0]=kind as u8;bytes[1]=1;
    if kind==0x30 {bytes[2]=1;}
    let checksum=crc::crc32::checksum_ieee(&bytes[..required-4]);
    bytes[required-4..].copy_from_slice(&checksum.to_le_bytes());
    required as i32
}

// Exact RoutingAck envelope only: length/CRC/kind are checked before accepting
// this payload-free variant; no generic Packet parser/allocation is needed.
#[no_mangle]
pub unsafe extern "C" fn aux_master_routing_ack_decode(buffer:*const u8,length:usize)->i32 {
    if buffer.is_null() || length!=8 {return -4;}
    let bytes=slice::from_raw_parts(buffer,length);
    let expected=crc::crc32::checksum_ieee(&bytes[..4]);
    let actual=(bytes[4] as u32)|((bytes[5] as u32)<<8)|((bytes[6] as u32)<<16)|((bytes[7] as u32)<<24);
    if expected!=actual {return -1;}
    if bytes[0]!=0x32 {return -2;}
    // Upstream RoutingAck has no payload. Exact envelope/CRC/kind validation
    // already determines it; avoid allocating the large generic Packet enum.
    // Host oracle compares this fixed-type path with unchanged upstream decode.
    0x32
}

// Canonical upstream default_master(1) table entry, separate from legacy
// experimental all-zero-tail leaf encoder. All256 destinations must be sent
// before rank1 when stale peer routing state cannot otherwise be excluded.
#[no_mangle]
pub unsafe extern "C" fn aux_master_star_path_encode(destination:u32,buffer:*mut u8,capacity:usize)->i32 {
 if buffer.is_null()||capacity<40||capacity>1024{return -4;}
 if destination>255{return -2;}
 let bytes=slice::from_raw_parts_mut(buffer,40);
 bytes.fill(0);bytes[0]=0x30;bytes[1]=destination as u8;
 bytes[2..34].fill(0xff);
 if destination==0 {bytes[2]=0;}
 if destination==1 {bytes[2]=1;bytes[3]=0;}
 let sum=crc::crc32::checksum_ieee(&bytes[..36]);
 bytes[36..40].copy_from_slice(&sum.to_le_bytes());
 40
}
