#!/usr/bin/env python3
"""Exact exception observer binary/layout gate; LGPL-3.0-or-later."""
import argparse
import json
import struct
from pathlib import Path
from package_local_candidate import loads
from check_el3_observer import WORDS
BASE=0xfffc8000
TAIL=WORDS+(0xd5384240,0xf100301f,0x54ffff81,0xd4200a60,0x17fffffa,
            0xd5384250,0xf100321f,0x54fffee1,0xd53e5211,0xd53e6012,
            0xd53e4033,0xd53e4014,0xd53b4235,0xd2801e6f,0x14000000)
SIZE=2048+4*len(TAIL)


def expected_payload():
    raw=bytearray(2048)
    for slot in range(16):
        offset=slot*128
        branch=0x14000000|((0x854-(offset+4))//4)
        struct.pack_into('<II',raw,offset,0xd280000e|(slot<<5),branch)
    return bytes(raw)+struct.pack('<'+str(len(TAIL))+'I',*TAIL)


def check(data):
    machine,entry,parts=loads(data)
    if machine!=183 or entry!=BASE+2048 or len(parts)!=1:
        raise ValueError('Unexpected observer architecture/entry/segments')
    p=parts[0]
    if (p['address'],p['vaddr'],p['filesz'],p['memsz'],p['flags'])!=(BASE,BASE,SIZE,SIZE,5):
        raise ValueError('Expected exact RX-only OCM extent, no data/BSS')
    if p['payload']!=expected_payload():
        raise ValueError('Vector/instruction drift: explicit review required')
    return dict(status='EXCEPTION_OBSERVER_STATIC_PASS',hardware_executed=False,
                vectors=hex(BASE),entry=hex(entry),bytes=SIZE,
                fault_probe=hex(BASE+0x840),success_terminal=hex(BASE+0x834),
                fault_terminal=hex(BASE+0x878),destructive_test_allowed=False,
                limits='Static only. Loader must install/read back VBAR_EL3 before continue; existing admission remains unchanged. No hardware fault/SError/DDR proof.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('elf',type=Path);a=p.parse_args()
    print(json.dumps(check(a.elf.read_bytes()),indent=2))
