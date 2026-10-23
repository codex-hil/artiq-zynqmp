#!/usr/bin/env python3
"""Offline APU reset-control observation plan; LGPL-3.0-or-later."""
import argparse
import hashlib
import json
from pathlib import Path
from plan_rpu_snapshot import expression

ADDRESS=0xfd1a0104


def plan(header):
    expected={'CRF_APB_BASEADDR':'0XFD1A0000U',
              'CRF_APB_RST_FPD_APU':'CRF_APB_BASEADDR+0X00000104U',
              'CRF_APB_RST_FPD_APU_APU_L2_RESET_MASK':'0X00000100U'}
    for i in range(4):
        expected[f'CRF_APB_RST_FPD_APU_ACPU{i}_RESET_MASK']=f'0X{1<<i:08X}U'
        expected[f'CRF_APB_RST_FPD_APU_ACPU{i}_PWRON_RESET_MASK']=f'0X{1<<(i+10):08X}U'
    for name,value in expected.items():
        if expression(header,name)!=value:raise ValueError('Changed APU definition '+name)
    return dict(status='OFFLINE_APU_RESET_PLAN_NOT_EXECUTED',hardware_executed=False,
                address=hex(ADDRESS),samples=2,width_bits=32,destructive_test_allowed=False,
                limits='Reset control read only. No reset writes, no cache/transaction-drain or PMU release exclusion proof.')


def decode(samples):
    if type(samples) is not list or len(samples)!=2 or any(type(v) is not int or not 0<=v<=0xffffffff for v in samples):
        raise ValueError('Two unsigned32-bit samples required')
    return dict(status='SUPPLIED_APU_RESET_CONTROLS_DECODED',hardware_executed=False,
                raw=samples,stable=samples[0]==samples[1],
                cores=[dict(core=i,reset_control_bits=[bool(v&(1<<i)) for v in samples],
                            power_on_reset_control_bits=[bool(v&(1<<(i+10))) for v in samples]) for i in range(4)],
                l2_reset_control_bits=[bool(v&0x100) for v in samples],
                unknown_bits=[v&~0x3d0f for v in samples],
                ownership='NOT_PROVEN',destructive_test_allowed=False)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--header',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=plan(a.header.read_text())
    r['input_sha256']={str(a.header):hashlib.sha256(a.header.read_bytes()).hexdigest()}
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open('x') as f:json.dump(r,f,indent=2);f.write('\n')
