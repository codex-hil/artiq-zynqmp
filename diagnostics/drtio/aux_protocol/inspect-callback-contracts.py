#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Source-reviewed callback contract for the isolated static caller ELF only."""
import argparse,hashlib,importlib.util,json,re
from pathlib import Path

def bind(text,frames,reviewed):
    spec=importlib.util.spec_from_file_location('graph',Path(__file__).with_name('inspect-caller-callgraph.py'))
    graph=importlib.util.module_from_spec(spec);spec.loader.exec_module(graph)
    targets={'read':['read_reg'],'write':['write_reg'],'fence':['fence'],'decode':['aux_master_control_decode','aux_master_routing_ack_decode']}
    # Function and register load reviewed against exact frozen disassembly.
    sites={'401a08':('map_step','fence','x1'),'401a48':('map_step','read','x3'),'401acc':('map_step','write','x3'),
           '400fa4':('mar_step','decode','x2'),'401030':('mar_step','read','x3'),'401118':('mar_step','fence','x1'),'4012c4':('mar_step','write','x3'),
           '4023bc':('mfc_poll','read','x3'),'402878':('mfc_poll','read','x3'),'403148':('mfc_poll','read','x3'),
           '4013e4':('mrs_step','fence','x1'),'401458':('mrs_step','read','x3'),'4014b0':('mrs_step','write','x3')}
    roots=['mfc_begin','mfc_poll','mfc_cancel','mfc_snapshot']+sum(targets.values(),[])
    rows=graph.inspect(text,frames,roots)
    frames.update({n:r['frame_bytes'] for n,r in reviewed['helpers'].items()})
    nodes={}
    for root in rows.values():nodes.update(root['reachable_functions'])
    seen=set();resolved=[]
    local={r['branch_address'][2:]:r for r in reviewed['computed_branches']}
    for name,row in nodes.items():
        row['frame_bytes']=frames.get(name,row['frame_bytes'])
        row['calls']=set(row['calls'])|set(row['tail_branches'])
        for site in row['indirect']:
            address=site['address']
            if site['instruction'].startswith('br '):
                assert address in local and local[address]['function']==name and local[address]['all_targets_local']
                continue
            assert address in sites,'New BLR site requires review'
            fn,role,reg=sites[address];assert fn==name and site['instruction']=='blr '+reg
            seen.add(address);row['calls'].update(targets[role]);resolved.append({'address':address,'function':name,'role':role,'conditional_targets':targets[role]})
    assert seen==set(sites),'Missing reviewed BLR site'
    for name,row in nodes.items():assert row['frame_bytes'] is not None,('Missing metadata',name)
    # Reject callback reentry, unknown transitive targets and recursive calls.
    def closure(name,trail=()):
        assert name not in trail,('Recursive call graph',trail,name)
        assert name in nodes,('Unresolved target',name)
        found={name}
        for target in nodes[name]['calls']:found|=closure(target,trail+(name,))
        return found
    for role,functions in targets.items():
        for name in functions:assert not (closure(name)&set(roots[:4])),'Callback reenters caller'
    def envelope(name):
        options=[envelope(n) for n in nodes[name]['calls']]
        child=max(options,key=lambda p:p[0]) if options else (0,[])
        return nodes[name]['frame_bytes']+child[0],[name]+child[1]
    sums={}
    for name in roots[:4]:
        closure(name);size,path=envelope(name);sums[name]={'conditional_sum_bytes':size,'path':path}
    return {'status':'ISOLATED_SOURCE_REVIEWED_CALLBACK_CONTRACT_PASS_NOT_RUNTIME_ADMISSION','sites':sorted(resolved,key=lambda x:x['address']),
            'callback_frames':{role:{n:nodes[n]['frame_bytes'] for n in values} for role,values in targets.items()},
            'conditional_frame_sums':sums,'callback_reentry_in_exact_mock_graph':False,
            'assumptions':['Exact frozen fixture initializes read_reg/write_reg/fence; copied bus pointers remain unchanged under sole foreground ownership','Decoder pointer originates only from two reviewed setup/star source assignments','No concurrency, corrupted pointers, unreviewed callbacks or reentry from outside this diagnostic ELF'],
            'limits':['Source-reviewed binding is not a general pointer-analysis or production callback enforcement proof','Sums conservatively add tail frames and mutually exclusive callback targets; exclude outer caller, IRQ/FPU/nesting and production runtime','No claim that active hardware EL/SP, worker handoff or recovery is qualified'],
            'runtime_admitted':False,'hardware_accessed':False,'complete_production_stack_bound_bytes':None}

def load_inputs(base):
    text=(base/'full-disassembly.txt').read_text()
    frames={n:int(v,16) for n,v in re.findall(r'Functions: \[(.*?)\]\s+Size: (0x[0-9a-fA-F]+)',(base/'stack-sizes.txt').read_text())}
    su={}
    for f in base.glob('*.su'):
        for line in f.read_text().splitlines():
            origin,size,qualifier=line.split('\t');assert qualifier=='static';su[origin.rsplit(':',1)[-1]]=int(size)
    for name in re.findall(r'^[0-9a-f]+ <([^>]+)>:',text,re.M):
        values={v for n,v in su.items() if name==n or name.startswith(n+'.')}
        if values:assert len(values)==1;frames[name]=values.pop()
    return text,frames

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--evidence',type=Path,required=True);p.add_argument('--helpers',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    base=a.evidence;text,frames=load_inputs(base)
    helpers=json.loads(a.helpers.read_text());assert helpers['input_sha256'][str(base/'full-disassembly.txt')]==hashlib.sha256((base/'full-disassembly.txt').read_bytes()).hexdigest()
    r=bind(text,frames,helpers)
    r['input_sha256']={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in [base/'full-disassembly.txt',base/'stack-sizes.txt',a.helpers]+sorted(base.glob('*.su'))}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,indent=2)+'\n');print(r['status']);print(r['conditional_frame_sums'])
if __name__=='__main__':main()
