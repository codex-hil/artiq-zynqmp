#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Exact retained diagnostic ELF helper-SP and bounded jump-table audit."""
import argparse,hashlib,json,re,struct
from pathlib import Path

def audit(elf,text,profile="original"):
    assert elf[:6]==b'\x7fELF\x02\x01','Need ELF64 little endian'
    assert struct.unpack_from('<H',elf,18)[0]==183,'Need AArch64'
    phoff=struct.unpack_from('<Q',elf,32)[0];ents,count=struct.unpack_from('<HH',elf,54)
    segments=[]
    for i in range(count):
        kind,flags,offset,va,pa,filesz,memsz,align=struct.unpack_from('<IIQQQQQQ',elf,phoff+i*ents)
        if kind==1:segments.append((va,offset,filesz))
    def read(address,n):
        for va,offset,size in segments:
            if va<=address and address+n<=va+size:return elf[offset+address-va:offset+address-va+n]
        raise ValueError('Address outside file-backed LOAD')
    functions={};current=None
    for line in text.splitlines():
        m=re.match(r'^([0-9a-f]+) <([^>]+)>:',line)
        if m:current=m[2];functions[current]={};continue
        m=re.match(r'^\s*([0-9a-f]+):\s+([0-9a-f]{8})\s+(\S+)\s*(.*)',line)
        if current is not None and m:
            addr=int(m[1],16);assert read(addr,4)==struct.pack('<I',int(m[2],16)),'Disassembly/ELF mismatch'
            functions[current][addr]=(m[3],m[4].split('//')[0].strip())
    helpers={}
    for name in ('memcpy','memset'):
        ins=functions[name];start=min(ins);pending=[(start,0)];states=set();returns=0;peak=0
        sp_lines=[(op,args) for op,args in ins.values() if re.search(r'\bsp\b',args)]
        assert sp_lines==[('stp','x29, x30, [sp, #-0x10]!'),('mov','x29, sp'),('ldp','x29, x30, [sp], #0x10')],sp_lines
        assert all(op not in ('bl','blr','br') for op,args in ins.values()),'Unexpected helper call'
        while pending:
            address,depth=pending.pop()
            if (address,depth) in states:continue
            assert address in ins,'Branch escaped helper'
            assert not any(a==address and d!=depth for a,d in states),'Inconsistent SP at CFG merge'
            states.add((address,depth));op,args=ins[address]
            if op=='stp' and '[sp, #-0x10]!' in args:depth+=16
            if op=='ldp' and '[sp], #0x10' in args:depth-=16
            assert 0<=depth<=16,'Unbounded/unbalanced helper SP';peak=max(peak,depth)
            if op=='ret':assert depth==0;returns+=1;continue
            if op=='b' or op.startswith('b.') or op in ('cbz','cbnz','tbz','tbnz'):
                m=re.search(r'0x([0-9a-f]+) <',args);assert m,'Unknown branch target'
                pending.append((int(m[1],16),depth))
                if op=='b':continue
            pending.append((address+4,depth))
        assert len({a for a,d in states})==len(ins),'Unvisited helper instructions'
        assert returns==1
        helpers[name]={'frame_bytes':peak,'all_instructions_cfg_checked':len(ins),'balanced_return_sites':returns,'calls':[]}
    tables=[]
    # Frozen compiler sequence and bounds check, tied to ELF bytes above.
    profiles={
        'original':[('mrs_step',0x401384,19,21,0x4013c4,0x4050a8,0x4013dc),('map_step',0x4017ec,10,23,0x4019e8,0x4050bc,0x401a00)],
        'network-static':[('mrs_step',0x401414,19,21,0x401454,0x405288,0x40146c),('map_step',0x40187c,10,23,0x401a78,0x40529c,0x401a90)],
        'reentry':[('mrs_step',0x401544,19,21,0x401584,0x405098,0x40159c),('map_step',0x4019ac,10,23,0x401ba8,0x4050ac,0x401bc0)]}
    for name,guard,limit,index,seq,table,base in profiles[profile]:
        ins=functions[name]
        assert ins[guard]==('cmp',f'w{index}, #0x{limit:x}')
        assert ins[guard+4][0]=='b.ls' and f'0x{seq:x} <' in ins[guard+4][1]
        expected=[('adrp','x0, 0x405000'),('add',f'x0, x0, #0x{table-0x405000:x}'),('ldrb',f'w0, [x0, w{index}, uxtw]'),('adr',f'x1, 0x{base:x}'),('add','x0, x1, w0, sxtb #2'),('br','x0')]
        for i,(op,prefix) in enumerate(expected):
            actual=ins[seq+4*i];assert actual[0]==op and (actual[1]==prefix or actual[1].startswith(prefix+' <')),(name,actual)
        raw=read(table,limit+1);targets=[base+4*struct.unpack('b',bytes([x]))[0] for x in raw]
        assert all(t in ins for t in targets),'Jump table escapes function/instruction boundary'
        tables.append({'function':name,'guard_address':hex(guard),'index_range':[0,limit],'branch_address':hex(seq+20),'table_address':hex(table),'table_hex':raw.hex(),'targets':[hex(t) for t in targets],'unique_targets':sorted({hex(t) for t in targets}),'all_targets_local':True})
    return {'helpers':helpers,'computed_branches':tables,'status':'EXACT_DIAGNOSTIC_HELPER_SP_AND_LOCAL_JUMP_TABLE_AUDIT_PASS','complete_stack_bound_bytes':None,'runtime_admitted':False,'hardware_accessed':False,'limits':['Exact retained diagnostic ELF only; not production memory helper implementation','Bounds/targets are static compiler sequence proof, not protection from corrupted control flow','13 indirect callsites and production caller/IRQ/nesting context remain unqualified']}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--elf',type=Path,required=True);p.add_argument('--disassembly',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--profile',choices=['original','reentry','network-static'],default='original');a=p.parse_args()
    r=audit(a.elf.read_bytes(),a.disassembly.read_text(),a.profile);r['input_sha256']={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in (a.elf,a.disassembly)}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,indent=2)+'\n');print(r['status'])
if __name__=='__main__':main()
