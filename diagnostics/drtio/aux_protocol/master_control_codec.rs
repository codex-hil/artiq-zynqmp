// SPDX-License-Identifier: LGPL-3.0-or-later
// Checked basic master candidate; host/isolated target only, not firmware service.
use core::slice;
#[no_mangle]
pub unsafe extern "C" fn aux_master_control_encode(kind:u32,value:u32,buffer:*mut u8,capacity:usize)->i32 {
 if buffer.is_null()||capacity<8||capacity>1024{return -4;}
 match(kind,value){(0,0)|(0x20,1)=>(),_=>return -2};
 let bytes=slice::from_raw_parts_mut(buffer,8);
 bytes.fill(0);bytes[0]=kind as u8;
 if kind==0x20 {bytes[1]=1;}
 let sum=crc::crc32::checksum_ieee(&bytes[..4]);
 bytes[4..8].copy_from_slice(&sum.to_le_bytes());
 8
}
// Exact fixed replies only. TSC ACK is received; never encoded as a time-set.
#[no_mangle]
pub unsafe extern "C" fn aux_master_control_decode(buffer:*const u8,length:usize)->i32 {
 if buffer.is_null()||length!=8{return -4;}
 let b=slice::from_raw_parts(buffer,length);
 let expected=crc::crc32::checksum_ieee(&b[..4]);
 let actual=(b[4] as u32)|((b[5] as u32)<<8)|((b[6] as u32)<<16)|((b[7] as u32)<<24);
 if expected!=actual{return -1;}
 // These four upstream reply variants have no payload. Do not instantiate
 // the generic Packet enum after strict fixed-envelope validation.
 match b[0]{1|4|0x21|0x22=>b[0] as i32,_=>-2}
}
