#!/usr/bin/env python3
"""Offline PCAP status/control context plan; LGPL-3.0-or-later."""
import argparse,json,hashlib
from pathlib import Path
from plan_pcap_snapshot import plan as status_plan,decode as status_decode
from plan_rpu_snapshot import expression
REGISTERS={'status':0xffca3010,'reset':0xffca300c,'control':0xffca3008,'direction':0xffca3004}

def plan(header):
    status_plan(header)
    for name,value in {'CSU_PCAP_RESET':'XILFPGA_CSU_BASEADDR+0X0000300CU',
                       'CSU_PCAP_CTRL':'XILFPGA_CSU_BASEADDR+0X00003008U',
                       'CSU_PCAP_RDWR':'XILFPGA_CSU_BASEADDR+0X00003004U',
                       'CSU_PCAP_RESET_RESET_MASK':'0X00000001U',
                       'CSU_PCAP_CTRL_PCAP_PR_MASK':'0X00000001U'}.items():
        if expression(header,name)!=value:raise ValueError('Changed PCAP control definition '+name)
    return dict(status='OFFLINE_PCAP_CONTEXT_PLAN_NOT_EXECUTED',hardware_executed=False,
                registers={n:hex(a) for n,a in REGISTERS.items()},samples=2,width_bits=32,
                destructive_test_allowed=False,
                limits='Read-only control/status context; no reset/mode/direction writes. Sampled reset control is not exclusive ownership; no automatic DDR admission.')

def decode(samples):
    if type(samples) is not list or len(samples)!=2:raise ValueError('Two complete samples required')
    for s in samples:
        if type(s) is not dict or set(s)!=set(REGISTERS) or any(type(v) is not int or not 0<=v<=0xffffffff for v in s.values()):raise ValueError('Exact unsigned32-bit context required')
    return dict(status='SUPPLIED_PCAP_CONTEXT_DECODED',hardware_executed=False,
                raw=samples,stable=samples[0]==samples[1],
                status_fields=status_decode([s['status'] for s in samples]),
                reset_control_bits=[bool(s['reset']&1) for s in samples],
                pcap_mode_bits=[bool(s['control']&1) for s in samples],
                direction_bits=[s['direction']&1 for s in samples],
                ownership='NOT_PROVEN',destructive_test_allowed=False,
                limits='Direction/reset context only. No inferred completion, held-reset permanence, outstanding memory drain or DDR admission.')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--header',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=plan(a.header.read_text());r['input_sha256']={str(a.header):hashlib.sha256(a.header.read_bytes()).hexdigest()}
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open('x') as f:json.dump(r,f,indent=2);f.write('\n')
