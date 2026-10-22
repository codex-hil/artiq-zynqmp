#!/usr/bin/env python3
"""Check supported DDR4 base-block CRC using Python's CRC primitive; LGPL-3.0-or-later."""
import argparse,binascii,hashlib,json
from pathlib import Path

def verify(data):
    if len(data)<128 or data[2]!=0x0c:raise ValueError('Require DDR4 base SPD block')
    # Limited DDR4 profile: reject unsupported high coverage/reserved bit rather
    # than silently applying the DDR3 shortened 117-byte coverage rule.
    if data[0]&0x80:raise ValueError('Unsupported DDR4 byte0 high-bit profile')
    computed=binascii.crc_hqx(data[:126],0)
    stored=int.from_bytes(data[126:128],'little')
    return dict(status='DDR4_BASE_CRC_VALID' if computed==stored else 'DDR4_BASE_CRC_FAIL',
        valid=computed==stored,covered_start=0,covered_bytes=126,stored=hex(stored),computed=hex(computed),
        polynomial='0x1021',initial='0x0',stored_byte_order='little',hardware_executed=False,
        spd_sha256=hashlib.sha256(data).hexdigest(),destructive_test_allowed=False,
        limits='Checks supplied DDR4 base bytes only. Does not establish EEPROM origin, full SPD semantics, module-block CRC, memory geometry or integrity.')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--spd',required=True,type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
    if a.output.exists():raise ValueError('Use fresh output')
    r=verify(a.spd.read_bytes());a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
    return 0 if r['valid'] else 1
if __name__=='__main__':raise SystemExit(main())
