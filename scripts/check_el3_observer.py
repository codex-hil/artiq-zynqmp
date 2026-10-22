#!/usr/bin/env python3
"""Exact register-only observer image gate; LGPL-3.0-or-later."""
import argparse
import json
import struct
from pathlib import Path
from package_local_candidate import loads

# Reviewed 16-instruction program, including both terminal branches. A source
# change requires explicit instruction review; mnemonic matching is insufficient.
WORDS = (0xd5384240, 0xf100301f, 0x54000181, 0xd53e1001,
         0xd53e1102, 0xd53c1003, 0xd5381004, 0xd53c1105,
         0xd53b4226, 0xd53800a7, 0x910003e8, 0x10fffea9,
         0xd280066f, 0x14000000, 0xd2801dcf, 0x14000000)


def check(data):
    machine, entry, segments = loads(data)
    if machine != 183 or entry != 0xfffc0000 or len(segments) != 1:
        raise ValueError('Unexpected observer entry/machine/segment count')
    s = segments[0]
    if (s['address'], s['vaddr'], s['filesz'], s['memsz'], s['flags']) != (entry, entry, 64, 64, 5):
        raise ValueError('Expected exactly 64 read/execute OCM bytes, no writable data/BSS')
    if s['payload'] != struct.pack('<16I', *WORDS):
        raise ValueError('Instruction drift: explicit review required')
    return dict(status='EXACT_REGISTER_ONLY_OCM_IMAGE_PASS', hardware_executed=False,
                destructive_test_allowed=False, entry=hex(entry), bytes=64,
                limits='Static image only. No trained handoff, runtime state or debugger download qualification.')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('elf', type=Path)
    a = p.parse_args()
    print(json.dumps(check(a.elf.read_bytes()), indent=2))
