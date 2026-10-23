#!/usr/bin/env python3
"""Conservative MicroBlaze exception call inventory, never DDR admission.
SPDX-License-Identifier: LGPL-3.0-or-later
"""
import argparse, hashlib, json, re
from pathlib import Path

def audit(text):
    blocks={}; current=None
    for line in text.splitlines():
        head=re.fullmatch(r'([0-9a-f]+) <([^>]+)>:',line)
        if head:
            current=int(head[1],16);blocks[current]={'name':head[2],'rows':[]}
        row=re.fullmatch(r'([0-9a-f]+):\s+([0-9a-f]{8})\s+(.*)',line)
        if row and current is not None:
            blocks[current]['rows'].append((int(row[1],16),int(row[2],16),row[3]))
    names={v['name']:k for k,v in blocks.items()}
    roots=['_vector_sw_exception','_vector_hw_exception']
    if any(n not in names for n in roots):raise ValueError('Missing exception vectors')
    pending=[names[n] for n in roots];seen=set();edges=[];unknown=[];memory=[];loops=[]
    while pending:
        start=pending.pop()
        if start in seen:continue
        seen.add(start)
        rows=blocks[start]['rows']
        for i,(pc,word,ins) in enumerate(rows):
            op=ins.split()[0]
            if op in ('brlid','brai','bralid','bri'):
                low=word&0xffff
                extended=i>0 and rows[i-1][1]>>16==0xb000
                delta=((rows[i-1][1]&0xffff)<<16)|low if extended else low
                bits=32 if extended else 16
                if delta&(1<<(bits-1)):delta-=1<<bits
                target=(delta if op in ('brai','bralid') else pc+delta)&0xffffffff
                if target==pc:loops.append(hex(pc))
                if target in blocks:
                    edges.append({'pc':hex(pc),'target':hex(target),'name':blocks[target]['name'],'op':op});pending.append(target)
                elif not start<=target<start+4*len(rows):unknown.append({'pc':hex(pc),'instruction':ins,'target':hex(target)})
            elif op.startswith('b') and op not in ('break','bslli','bsrli','bsrai','bsll','bsrl','bsra'):
                unknown.append({'pc':hex(pc),'instruction':ins,'reason':'Unresolved register/unsupported branch'})
            if op in ('lwi','lw','lbui','lhu','lhui','lbu','swi','sw','sbi','sb','shi','sh'):
                memory.append({'pc':hex(pc),'instruction':ins,'classification':'Address not proven by this inventory'})
    return {'status':'OFFLINE_EXCEPTION_INVENTORY_NOT_EXCLUSION_PROOF','hardware_executed':False,'destructive_test_allowed':False,'functions':[{'start':hex(k),'name':blocks[k]['name']} for k in sorted(seen)],'direct_edges':edges,'unresolved_control':unknown,'memory_operations':memory,'self_loops':loops,'limits':'Function-level direct-edge overapproximation, not instruction reachability or register/dataflow analysis. Conditional targets, indirect calls, ROM/reset/NMI and stack bounds require separate proof. All memory effective addresses remain unresolved.'}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--disassembly',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    data=a.disassembly.read_bytes();result=audit(data.decode());result['disassembly_sha256']=hashlib.sha256(data).hexdigest()
    with a.output.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
