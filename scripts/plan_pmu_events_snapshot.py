#!/usr/bin/env python3
"""Offline PMU event observation plan; LGPL-3.0-or-later."""
import argparse,hashlib,json
from pathlib import Path
from plan_rpu_snapshot import expression
REGISTERS={'gpi1':0xffd40024,'gpi2':0xffd40028,'irq_pending':0xffd40034,
           'irq_enable':0xffd40038,'gpi1_enable':0xffd60224,'gpi2_enable':0xffd60228}


def plan(iomodule,local):
    for text,prefix,base,regs in [
        (iomodule,'PMU_IOMODULE',0xffd40000,{'GPI1':0x24,'GPI2':0x28,'IRQ_PENDING':0x34,'IRQ_ENABLE':0x38}),
        (local,'PMU_LOCAL',0xffd60000,{'GPI1_ENABLE':0x224,'GPI2_ENABLE':0x228})]:
        if expression(text,prefix+'_BASEADDR')!=f'0X{base:08X}U':raise ValueError('Changed PMU base')
        for n,o in regs.items():
            if expression(text,prefix+'_'+n)!=f'{prefix}_BASEADDR+0X{o:08X}U':raise ValueError('Changed PMU register '+n)
    for i in range(4):
        for text,n in [(iomodule,f'PMU_IOMODULE_GPI1_ACPU_{i}_WAKE_MASK'),(local,f'PMU_LOCAL_GPI1_ENABLE_ACPU{i}_WAKE_MASK')]:
            if expression(text,n)!=f'0X{1<<i:08X}U':raise ValueError('Changed wake field')
    for i in range(2):
        for text,n in [(iomodule,f'PMU_IOMODULE_GPI1_R5_{i}_WAKE_MASK'),(local,f'PMU_LOCAL_GPI1_ENABLE_R5_{i}_WAKE_MASK')]:
            if expression(text,n)!=f'0X{1<<(i+4):08X}U':raise ValueError('Changed R5 wake field')
    return dict(status='OFFLINE_PMU_EVENT_PLAN_NOT_EXECUTED',hardware_executed=False,
                registers={n:hex(a) for n,a in REGISTERS.items()},width_bits=32,samples=2,
                destructive_test_allowed=False,
                limits='Read-only observations; omit IRQ_ACK, IPI ISR acknowledgements, enables/disables and event writes. DAP access not proven; no force-access fallback. Zero pending is not future-wake exclusion.')


def decode(samples):
    if type(samples) is not list or len(samples)!=2:raise ValueError('Two complete samples required')
    for s in samples:
        if type(s) is not dict or set(s)!=set(REGISTERS) or any(type(v) is not int or not 0<=v<=0xffffffff for v in s.values()):raise ValueError('Exact unsigned32-bit set required')
    return dict(status='SUPPLIED_PMU_EVENT_FIELDS',hardware_executed=False,
                raw=samples,stable=samples[0]==samples[1],
                processor_wake_signal_bits=[s['gpi1']&0x3f for s in samples],
                processor_wake_enable_bits=[s['gpi1_enable']&0x3f for s in samples],
                processor_wake_signal_and_enable=[s['gpi1']&s['gpi1_enable']&0x3f for s in samples],
                ownership='NOT_PROVEN',destructive_test_allowed=False)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ['iomodule','local','output']:p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();r=plan(a.iomodule.read_text(),a.local.read_text())
    r['input_sha256']={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in [a.iomodule,a.local]}
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open('x') as f:json.dump(r,f,indent=2);f.write('\n')
