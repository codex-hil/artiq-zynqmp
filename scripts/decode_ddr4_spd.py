#!/usr/bin/env python3
"""Limited DDR4 SPD geometry per Piotr/AMD FSBL; LGPL-3.0-or-later."""
import argparse,hashlib,json
from pathlib import Path
from check_ddr4_spd_crc import verify as verify_crc


def decode(data,require_crc=False):
    crc_report=verify_crc(data) if require_crc else None
    if crc_report is not None and not crc_report["valid"]:raise ValueError("DDR4 base CRC mismatch")
    if len(data)<128 or data[2]!=0x0c:raise ValueError('Require DDR4 base SPD block')
    if data[6]!=0 or data[12]&0xc0:raise ValueError('Only symmetric monolithic package supported')
    density=data[4]&15;bus=data[13]&7;device=data[12]&7;ranks=((data[12]>>3)&7)+1
    if density>7 or bus>3 or device>3 or ranks not in (1,2) or data[3]&15 not in (2,3):
        raise ValueError('Unsupported density/width/rank/module geometry')
    rows=((data[5]>>3)&7)+12;columns=(data[5]&7)+9;banks=((data[4]>>4)&3)+2;groups=(data[4]>>6)&3
    rank_bytes=1<<(density+28-3+(bus+3)-(device+2))
    # Byte capacity from address geometry: locations per device times primary bus bytes.
    addressed_rank_bytes=(1<<(rows+columns+banks+groups))*(1<<(bus+3))//8
    if rank_bytes!=addressed_rank_bytes:raise ValueError('SPD density and address geometry disagree')
    return dict(status='SPD_GEOMETRY_DECODED_BASE_CRC_VALID' if require_crc else 'SPD_GEOMETRY_DECODED_CRC_NOT_VERIFIED',hardware_executed=False,
        primary_bus_bits=1<<(bus+3),device_dq_bits=1<<(device+2),ranks=ranks,
        row_bits=rows,column_bits=columns,bank_bits=banks,bank_group_bits=groups,
        rank_bytes=rank_bytes,module_bytes=rank_bytes*ranks,crc='BASE_VALID' if require_crc else 'NOT_VERIFIED',crc_report=crc_report,destructive_test_allowed=False,
        limits='Limited symmetric monolithic UDIMM/SODIMM geometry. No EEPROM acquisition, module-block CRC, controller agreement or physical memory proof. Base CRC checked only when explicitly required.')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--spd',required=True,type=Path);p.add_argument('--output',required=True,type=Path);p.add_argument('--require-crc',action='store_true');a=p.parse_args()
    if a.output.exists():raise ValueError('Use fresh output')
    data=a.spd.read_bytes();r=decode(data,require_crc=a.require_crc);r['spd_sha256']=hashlib.sha256(data).hexdigest();a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open('x') as f:f.write(json.dumps(r,indent=2)+'\n')
    print(json.dumps(r,indent=2))

if __name__=='__main__':main()
