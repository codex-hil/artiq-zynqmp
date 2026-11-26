#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Inventory diagnostic A53 call edges; unresolved callbacks forbid a stack bound."""
import argparse,hashlib,json,re
from pathlib import Path

def inspect(disassembly, frames, roots):
    functions={}; current=None
    for line in disassembly.splitlines():
        match=re.match(r'^([0-9a-f]+) <([^>]+)>:',line)
        if match:
            current=match[2];functions[current]={'calls':set(),'tails':set(),'indirect':[]}
            continue
        if current is None:continue
        ins=re.match(r'^\s*([0-9a-f]+):\s+[0-9a-f]+\s+(bl|blr|b(?:\.[a-z]+)?|br)\s+(.+)',line)
        if not ins:continue
        address,op,args=ins.groups()
        if op in ('blr','br'):
            functions[current]['indirect'].append({'address':address,'instruction':op+' '+args.strip()})
            continue
        target=re.search(r'<([^>]+)>',args)
        if not target:raise ValueError('Unresolved direct branch: '+line)
        name=target[1].split('+0x')[0]
        if op=='bl':functions[current]['calls'].add(name)
        elif name!=current:functions[current]['tails'].add(name)
    reports={}
    for root in roots:
        if root not in functions:raise ValueError('Missing root '+root)
        reached=set();pending=[root]
        while pending:
            name=pending.pop()
            if name in reached:continue
            reached.add(name)
            if name in functions:pending.extend(functions[name]['calls']|functions[name]['tails'])
        rows={name:{'frame_bytes':frames.get(name),'calls':sorted(functions.get(name,{}).get('calls',[])),
                    'tail_branches':sorted(functions.get(name,{}).get('tails',[])),
                    'indirect':functions.get(name,{}).get('indirect',[])} for name in sorted(reached)}
        missing=[name for name,row in rows.items() if row['frame_bytes'] is None]
        indirect={name:row['indirect'] for name,row in rows.items() if row['indirect']}
        # A graph inventory deliberately avoids adding frame sizes across tail
        # branches, mutually exclusive paths, or unknown indirect callbacks.
        reports[root]={'reachable_functions':rows,'missing_frame_metadata':missing,
                       'unresolved_indirect_sites':indirect,'complete_stack_bound_bytes':None}
    return reports

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--disassembly',type=Path,required=True);p.add_argument('--stack-sizes',type=Path,required=True)
    p.add_argument('--su',type=Path,action='append',default=[]);p.add_argument('--elf',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    frames={name:int(size,16) for name,size in re.findall(r'Functions: \[(.*?)\]\s+Size: (0x[0-9a-fA-F]+)',a.stack_sizes.read_text())}
    suframes={}
    for path in a.su:
        for line in path.read_text().splitlines():
            origin,size,qualifier=line.split('\t');name=origin.rsplit(':',1)[-1]
            if qualifier!='static':raise ValueError('Nonstatic C frame '+line)
            suframes[name]=int(size)
    text=a.disassembly.read_text()
    for name in re.findall(r'^[0-9a-f]+ <([^>]+)>:',text,re.M):
        matches=[size for candidate,size in suframes.items() if name==candidate or name.startswith(candidate+'.')]
        if matches:
            if len(set(matches))!=1:raise ValueError('Ambiguous frame '+name)
            frames[name]=matches[0]
    roots=['mfc_begin','mfc_poll','mfc_cancel','mfc_snapshot']
    report={'status':'DIAGNOSTIC_CALLGRAPH_INVENTORY_NOT_STACK_QUALIFICATION','roots':inspect(text,frames,roots),
            'hardware_accessed':False,'runtime_admitted':False,'complete_stack_bound_bytes':None,
            'limits':['Exact diagnostic ELF only; not production lwIP/IRQ caller','Indirect bus/decoder callbacks require explicit target contracts; never assume zero stack','Tail branches inventoried separately; no naive additive frame bound','Retained IRQ assembly 208 B is only a pre-C lower bound, not nesting/handler budget','Production active EL/SP, IRQ masking/nesting and complete callbacks remain unqualified'],
            'input_sha256':{str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in [a.elf,a.disassembly,a.stack_sizes]+a.su}}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n')
    for name,row in report['roots'].items():print(name,'reachable',len(row['reachable_functions']),'indirect_functions',len(row['unresolved_indirect_sites']),'missing_frames',len(row['missing_frame_metadata']))
if __name__=='__main__':main()
