#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Exact network-static ELF: conditional mock/observer/recursion frame sums."""
import argparse,hashlib,importlib.util,json,re,subprocess
from pathlib import Path

def load(name,file):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def inspect(base):
    elf=base/'codec-normal.elf';text=(base/'full-disassembly.txt').read_text()
    assert subprocess.check_output(['/srv/codex-hil-data/artiq-zynqmp/toolchains/abi-verified/root/usr/bin/llvm-objdump-19','-d',str(elf)],text=True)==text
    receipt=json.loads((base/'execution-results.json').read_text());assert hashlib.sha256(elf.read_bytes()).hexdigest()==receipt['runs']['normal']['elf_sha256']
    helpers=load('helpers','inspect-linked-helpers.py').audit(elf.read_bytes(),text,'network-static')
    _,frames=load('frames','inspect-callback-contracts.py').load_inputs(base)
    frames.update({n:r['frame_bytes'] for n,r in helpers['helpers'].items()})
    ins={int(m[1],16):(m[2],m[3].split('//')[0].strip()) for m in re.finditer(r'^\s*([0-9a-f]+):\s+[0-9a-f]{8}\s+(\S+)[ \t]*(.*)',text,re.M)}
    paths={'mns_begin':list(range(0x4022d0,0x4022f4,4))+[0x402668,0x40266c]+list(range(0x4023dc,0x4023f4,4)),
           'mns_poll':list(range(0x4026a0,0x4026c8,4))+[0x4029d4,0x4029d8]+list(range(0x4026d0,0x4026e4,4)),
           'mns_snapshot':list(range(0x4038e0,0x403904,4))+[0x403a20,0x403a24]+list(range(0x403930,0x403940,4))}
    guards={'mns_begin':(0x4022ec,('ldr','w26, [x19, #0x134c]'),0x4022f0,'w26','0x402668','w9'),
            'mns_poll':(0x4026c0,('ldr','w0, [x21, #0x134c]'),0x4026c4,'w0','0x4029d4','w19'),
            'mns_snapshot':(0x4038fc,('ldr','w0, [x19, #0x134c]'),0x403900,'w0','0x403a20','w0')}
    rejects={}
    for name,path in paths.items():
        address,expected,branch,reg,dest,busy=guards[name];assert ins[address]==expected
        assert ins[branch][0]=='cbnz' and ins[branch][1].startswith(reg+', '+dest+' <')
        assert any(ins[a]==('mov',busy+', #-0x2') for a in path)
        if busy!='w0':assert any(ins[a]==('mov','w0, '+busy) for a in path)
        depth=peak=0;proof=[]
        for i,a in enumerate(path):
            op,args=ins[a];proof.append({'address':hex(a),'instruction':op+' '+args})
            assert op in ('stp','str','ldp','ldr','mov','adrp','add','cbnz','cbz','b','ret')
            if op in ('stp','str'):assert '[sp,' in args,'Nonstack write in rejected entry'
            if op=='stp' and ']!' in args:depth+=int(re.search(r'#-0x([0-9a-f]+)',args)[1],16)
            if op=='ldp' and '[sp], #' in args:depth-=int(re.search(r'\[sp\], #0x([0-9a-f]+)',args)[1],16)
            assert depth>=0;peak=max(peak,depth)
            if op in ('b','cbnz'):assert int(re.search(r'0x([0-9a-f]+)',args)[1],16)==path[i+1]
            if op=='cbz':assert a==0x4026bc and path[i+1]==a+4 # started!=0 at callback recursion
        assert depth==0 and ins[path[-1]][0]=='ret'
        rejects[name]={'frame_bytes':peak,'condition':'active!=0; poll additionally started!=0','instructions':proof,'calls':[],'nonstack_writes':False}
        frames[name+'[active]']=peak
    roots=['mns_begin','mns_poll','mns_snapshot','rd','wr','fence','health','probe','aux_master_control_decode','aux_master_routing_ack_decode']
    graph=load('graph','inspect-caller-callgraph.py').inspect(text,frames,roots);nodes={}
    for row in graph.values():nodes.update(row['reachable_functions'])
    # Exact frozen role mapping; source/bus initialization is a reviewed fixture
    # contract, not a general dynamic pointer-analysis result.
    sites={0x401a98:('fence','x1'),0x401ad8:('read','x3'),0x401b5c:('write','x3'),0x401034:('decode','x2'),0x4010c0:('read','x3'),0x4011a8:('fence','x1'),0x401354:('write','x3'),0x402920:('read','x3'),0x402d00:('read','x3'),0x40382c:('read','x3'),0x401474:('fence','x1'),0x4014e8:('read','x3'),0x401540:('write','x3'),0x402184:('observer','x2'),0x402344:('observer','x4')}
    targets={'read':['rd'],'write':['wr'],'fence':['fence'],'observer':['health'],'decode':['aux_master_control_decode','aux_master_routing_ack_decode']}
    local={int(r['branch_address'],16) for r in helpers['computed_branches']};seen=set()
    for name,row in nodes.items():
        calls=set(row['calls'])|set(row['tail_branches'])
        if name=='probe':calls={n+'[active]' if n in rejects else n for n in calls}
        row['calls']=calls;row['frame_bytes']=frames.get(name,row['frame_bytes']);assert row['frame_bytes'] is not None,('Missing frame',name)
        for site in row['indirect']:
            address=int(site['address'],16)
            if site['instruction'].startswith('br '):assert address in local;continue
            assert address in sites,('Unreviewed callback site',site)
            role,reg=sites[address];assert site['instruction']=='blr '+reg;seen.add(address);calls.update(targets[role])
    assert seen==set(sites)
    for n,r in rejects.items():nodes[n+'[active]']={'calls':set(),'frame_bytes':r['frame_bytes']}
    def envelope(name,trail=()):
        assert name not in trail,('Unresolved cycle',trail,name)
        paths=[envelope(n,trail+(name,)) for n in nodes[name]['calls']]
        amount,path=max(paths,key=lambda x:x[0]) if paths else (0,[])
        return nodes[name]['frame_bytes']+amount,[name]+path
    sums={n:dict(zip(('bytes','path'),envelope(n))) for n in roots[:3]}
    return {'status':'NETWORK_STATIC_CONDITIONAL_OBSERVER_AND_REENTRY_STACK_AUDIT_PASS','rejected_entry_paths':rejects,'conditional_frame_sums':sums,'resolved_indirect_sites':len(seen),'helpers':helpers['helpers'],'jump_table_entries':31,'runtime_admitted':False,'hardware_accessed':False,'complete_production_stack_bound_bytes':None,'assumptions':['Frozen mock bus and memory observer targets, same source/layout/ownership contract as executed test','Only probe recurses into public API while active remains nonzero; poll has started!=0','Static compiler frames plus resolved Rust metadata; tail edges conservatively added'],'limits':['Exact diagnostic ELF, not production observer/IRQ/worker integration','No IRQ/GEM recovery nesting, FPU trap, exception/unwind or liveEL/SP qualification','Conditional graph sum excludes outer caller and interrupts, not an observed high-water measurement'],'frame_metadata':{n:r['frame_bytes'] for n,r in nodes.items()},'input_sha256':{str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in [elf,base/'full-disassembly.txt',base/'stack-sizes.txt',base/'execution-results.json']+sorted(base.glob('codec-normal*.su'))}}

def main():
    p=argparse.ArgumentParser();p.add_argument('--artifacts',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=inspect(a.artifacts);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,indent=2)+'\n');print(r['status']);print(r['conditional_frame_sums'])
if __name__=='__main__':main()
