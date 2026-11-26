#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Bind BSP frame probes to exact instruction bytes and relocation meaning."""
import argparse,hashlib,importlib.util,json,struct
from pathlib import Path

def relocs(path,source_alias=None):
    b=path.read_bytes();off=struct.unpack_from('<Q',b,40)[0];size,count,names=struct.unpack_from('<HHH',b,58)
    h=[struct.unpack_from('<IIQQQQIIQQ',b,off+i*size) for i in range(count)]
    data=lambda x:b[x[4]:x[4]+x[5]]
    strings=data(h[names]);cstr=lambda s,n:s[n:s.index(b'\0',n)]
    named={cstr(strings,x[0]).decode():x for x in h};r=named['.rela.text'];sym=h[r[6]];st=data(h[sym[6]]);result=[]
    for at in range(0,r[5],24):
        pos,info,addend=struct.unpack_from('<QQq',data(r),at);si=info>>32;kind=info&0xffffffff
        name,flags,other,section,value,length=struct.unpack_from('<IBBHQQ',data(sym),si*24)
        name=cstr(st,name).decode();target=[name,value,addend]
        if section<len(h) and section>0 and kind in (275,277):
            sn=cstr(strings,h[section][0]).decode();d=data(h[section]);index=value+addend
            if sn.startswith('.rodata') and 0<=index<len(d):
                text=cstr(d,index)
                if text and all(x in (9,10,13) or 32<=x<127 for x in text):
                    value=text.decode();target=['readonly_string','REVIEWED_SOURCE_FILENAME' if value==source_alias else value]
        result.append([pos,kind,target])
    return result

def main():
    p=argparse.ArgumentParser();p.add_argument('--baseline',type=Path,required=True);p.add_argument('--probe',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    spec=importlib.util.spec_from_file_location('reader',Path(__file__).with_name('inspect-retained-caller.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    rows=[];frames={};sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    for row in json.loads((a.baseline/'bindings.json').read_text()):
        old=Path(row['retained_object']);new=a.probe/row['probe_object'];left,right=m.sections(old),m.sections(new)
        assert left['.text']==right['.text'],('Instruction mismatch',new.name)
        commands=json.loads((a.probe/'commands.json').read_text())
        aliases=[arg for cmd in commands for arg in cmd if arg.endswith('/'+Path(row['source']).name)]
        assert len(aliases)==1
        assert relocs(old,row['source'])==relocs(new,aliases[0]),('Relocation meaning mismatch',new.name)
        rows.append({'source':row['source'],'source_sha256':row['source_sha256'],'retained_object_sha256':sha(old),'probe_object_sha256':sha(new),'instruction_bytes_identical':True,'canonical_relocations_identical':True,'raw_relocations_identical':left['.rela.text']==right['.rela.text']})
    for f in a.probe.glob('*.su'):
        for line in f.read_text().splitlines():
            name,size,qualifier=line.split('\t');assert qualifier=='static';frames[name.rsplit(':',1)[-1]]=int(size)
    r={'status':'SEVEN_BSP_IRQ_FRAME_PROBES_INSTRUCTION_AND_RELOCATION_MEANING_PASS','bindings':rows,'frame_bytes':frames,'runtime_admitted':False,'hardware_accessed':False,'limits':['Readonly string relocations resolved by content; only exact recorded __FILE__ path replaced by reviewed filename marker; raw differences retained','Per-function frames only; no transitive callback/IRQ/nesting/activeEL-SP bound','First probe batch used stale nonoptimized compilation database and is not admitted']}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,indent=2)+'\n');print(r['status'])
if __name__=='__main__':main()
