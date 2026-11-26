#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Exact A53 sticky-latch instruction contract; not hardware IRQ validation."""
import argparse,hashlib,importlib.util,json,struct
from pathlib import Path

def check(text):
    words=list(struct.unpack('<'+'I'*(len(text)//4),text))
    assert words[:3]==[0x52800021,0x889ffc01,0xd65f03c0],'Publish must store1-release and return without calls/loops'
    assert words[4:8]==[0x88dffc00,0x7100001f,0x1a9f07e0,0xd65f03c0],'Seen must load-acquire and return boolean'
    assert words[0x48//4]==0x88dffc40,'Observer must load-acquire'
    assert len(text)==0x6c,'Code shape changed; review required'

def main():
    p=argparse.ArgumentParser();p.add_argument('--artifacts',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    spec=importlib.util.spec_from_file_location('elf',str(Path(__file__).with_name('inspect-retained-caller.py')));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    obj=a.artifacts/'probe.o';code=m.sections(obj)['.text'];check(code)
    assert not (a.artifacts/'undefined.txt').read_text().strip(),'Unexpected runtime/atomic helper'
    frames={}
    for f in a.artifacts.glob('*.su'):
        for line in f.read_text().splitlines():
            name,size,kind=line.split('\t');assert kind=='static';frames[name.rsplit(':',1)[-1]]=int(size)
    assert frames=={'mnf_probe_publish':0,'mnf_probe_seen':0,'mnf_probe_observe':0}
    mutants={'relaxed-publish':(4,0xb9000001),'relaxed-read':(0x10,0xb9400000),'relaxed-observer':(0x48,0xb9400040)}
    for name,(offset,word) in mutants.items():
        changed=bytearray(code);struct.pack_into('<I',changed,offset,word)
        try:check(changed)
        except AssertionError:pass
        else:raise AssertionError('Weakened atomic instruction accepted: '+name)
    r={'status':'A53_RELEASE_ACQUIRE_ZERO_FRAME_NO_HELPERS_AND_THREE_WEAKENED_INSTRUCTION_REFUSALS_PASS','frames_bytes':frames,'publish_instructions':3,'publisher':'MOV1/STLR/RET; no RMW or retry loop','read':'LDAR + boolean conversion; observer also uses LDAR','mutants_refused':list(mutants),'object_sha256':hashlib.sha256(obj.read_bytes()).hexdigest(),'hardware_accessed':False,'limits':['Exact code shape under CortexA53 -O2 -mgeneral-regs-only only','No producer/observer installed in IRQ or deployed runtime','Normal coherent memory, lifetime and immutable view qualifications remain external','Concurrency stress test and codegen are not exhaustive weak-memory, IRQ nesting or atomic success-vs-fault proof']}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,indent=2)+'\n');print(r['status'])
if __name__=='__main__':main()
