#!/usr/bin/env python3
"""Offline AMD PCAP status plan, not ownership; LGPL-3.0-or-later."""
import argparse,hashlib,json
from pathlib import Path
from plan_rpu_snapshot import expression
ADDRESS=0xffca3010
FIELDS={'write_idle':1,'read_idle':2,'pl_init':4,'pl_done':8}

def plan(header):
    expected={'XILFPGA_CSU_BASEADDR':'0XFFCA0000U',
              'CSU_PCAP_STATUS':'XILFPGA_CSU_BASEADDR+0X00003010U',
              'PCAP_STATUS_PCAP_WR_IDLE_MASK':'0X00000001U',
              'PCAP_STATUS_PCAP_RD_IDLE_MASK':'0X00000002U',
              'CSU_PCAP_STATUS_PL_INIT_MASK':'0X00000004U',
              'CSU_PCAP_STATUS_PL_DONE_MASK':'0X00000008U'}
    for name,value in expected.items():
        if expression(header,name)!=value:raise ValueError('Changed PCAP definition '+name)
    return dict(status='OFFLINE_PCAP_STATUS_PLAN_NOT_EXECUTED',hardware_executed=False,
                address=hex(ADDRESS),samples=2,width_bits=32,destructive_test_allowed=False,
                limits='Status read only. No PROGRAM/RDWR/RESET/CTRL/interrupt writes, no configuration readback. Idle is momentary, not exclusive ownership or PS drain.')


def decode(samples):
    if type(samples) is not list or len(samples)!=2 or any(type(v) is not int or not 0<=v<=0xffffffff for v in samples):
        raise ValueError('Two unsigned32-bit PCAP values required')
    return dict(status='SUPPLIED_PCAP_STATUS_FIELDS',hardware_executed=False,raw=samples,
                stable=samples[0]==samples[1],fields={n:[bool(v&m) for v in samples] for n,m in FIELDS.items()},
                other_status_bits=[v&0xfffffff0 for v in samples],
                sampled_read_write_idle=all(v&3==3 for v in samples),
                ownership='NOT_PROVEN',destructive_test_allowed=False)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--header',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=plan(a.header.read_text());r['input_sha256']={str(a.header):hashlib.sha256(a.header.read_bytes()).hexdigest()}
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open('x') as f:json.dump(r,f,indent=2);f.write('\n')
