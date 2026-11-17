// SPDX-License-Identifier: LGPL-3.0-or-later
// Isolated single-leaf master encoder candidate; not linked into firmware.
use core::slice;
use io::{Cursor, ProtoWrite};
use protocol::Packet;

// Only destination1 over port1/rank1 is admitted by this candidate contract.
// Invalid arguments leave output untouched; caller supplies a valid writable buffer.
#[no_mangle]
pub unsafe extern "C" fn aux_master_leaf_encode(kind:u32,value:u32,buffer:*mut u8,capacity:usize)->i32 {
    if buffer.is_null() || capacity>1024 {return -4;}
    let (packet,required)=match (kind,value) {
        (0x30,1)=>{let mut hops=[0u8;32];hops[0]=1;
            (Packet::RoutingSetPath{destination:1,hops:hops},40)},
        (0x31,1)=>(Packet::RoutingSetRank{rank:1},8),
        _=>return -2,
    };
    if capacity<required {return -4;}
    let mut writer=Cursor::new(slice::from_raw_parts_mut(buffer,capacity));
    if packet.write_to(&mut writer).is_err(){return -3;}
    let padding=(12-writer.position()%8)%8;
    for _ in 0..padding {if writer.write_u8(0).is_err(){return -3;}}
    let checksum=crc::crc32::checksum_ieee(&writer.get_ref()[..writer.position()]);
    if writer.write_u32(checksum).is_err(){return -3;}
    writer.position() as i32
}
