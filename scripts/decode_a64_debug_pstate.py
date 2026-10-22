#!/usr/bin/env python3
"""Decode supplied AArch64 debug PSTATE, never admit execution; LGPL-3.0-or-later."""
import argparse
import json


def decode(value):
    if type(value) is not int or not 0 <= value <= 0xffffffff:
        raise ValueError('Expected 32-bit debug PSTATE')
    mode=value & 31
    modes={0:'EL0t',4:'EL1t',5:'EL1h',8:'EL2t',9:'EL2h',12:'EL3t',13:'EL3h'}
    if mode not in modes:
        raise ValueError('AArch32/reserved mode is not an AArch64 PSTATE observation')
    masks={name:bool(value & (1 << bit)) for name,bit in [('D',9),('A',8),('I',7),('F',6)]}
    return dict(status='SUPPLIED_AARCH64_PSTATE_DECODED',hardware_executed=False,
                raw=hex(value),mode=modes[mode],currentel_encoding=mode & 12,
                daif=hex(value & 0x3c0),masked=masks,
                required_observer_masks_present=all(masks.values()),
                destructive_test_allowed=False,
                limits='Supplied debug CPSR/PSTATE data, not SPSR_EL3. No debugger provenance/cache/ownership or execution admission.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('value',type=lambda s:int(s,0));a=p.parse_args()
    print(json.dumps(decode(a.value),indent=2))
