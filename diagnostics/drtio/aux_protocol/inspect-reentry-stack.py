#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-3.0-or-later
"""State-conditioned frame sum for the exact reentry-probing diagnostic ELF."""
import argparse,hashlib,importlib.util,json,re,subprocess
from pathlib import Path

def module(name,file):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def inspect(base):
    elf=base/'codec-normal.elf';text=(base/'full-disassembly.txt').read_text()
    tool='/srv/codex-hil-data/artiq-zynqmp/toolchains/abi-verified/root/usr/bin/llvm-objdump-19'
    assert subprocess.check_output([tool,'-d',str(elf)],text=True)==text,'Disassembly not reproduced'
    expected=json.loads((base/'execution-results.json').read_text())['runs']['normal']['elf_sha256']
    assert hashlib.sha256(elf.read_bytes()).hexdigest()==expected,'Execution/ELF mismatch'
    helpers=module('helpers','inspect-linked-helpers.py').audit(elf.read_bytes(),text,'reentry')
    _,frames=module('contracts','inspect-callback-contracts.py').load_inputs(base)
    frames.update({n:v['frame_bytes'] for n,v in helpers['helpers'].items()})
    instructions={int(m[1],16):(m[2],m[3].split('//')[0].strip()) for m in re.finditer(r'^\s*([0-9a-f]+):\s+[0-9a-f]{8}\s+(\S+)[ \t]*(.*)',text,re.M)}
    # Explicit active!=0 paths reviewed against this ELF, not arbitrary future builds.
    paths={'mfc_begin':list(range(0x402290,0x4022ac,4))+[0x402474,0x402478],
           'mfc_poll':list(range(0x4024a0,0x4024b8,4))+[0x402814,0x402818,0x40250c,0x402510,0x402514],
           'mfc_cancel':[0x4035d0,0x4035d4,0x4035d8,0x403778,0x40377c],
           'mfc_snapshot':[0x403790,0x403794,0x403798,0x4038b8,0x4038bc]}
    guards={'mfc_begin':(0x40229c,'w9, [x11, #0x200]',0x4022a8,'w9','0x402474'),
            'mfc_poll':(0x4024b0,'w0, [x20, #0x200]',0x4024b4,'w0','0x402814'),
            'mfc_cancel':(0x4035d4,'w0, [x9, #0x200]',0x4035d8,'w0','0x403778'),
            'mfc_snapshot':(0x403794,'w1, [x1, #0x200]',0x403798,'w1','0x4038b8')}
    rejected={}
    for name,path in paths.items():
        load,args,branch,reg,dest=guards[name]
        assert instructions[load]==('ldr',args)
        op,arg=instructions[branch];assert op=='cbnz' and arg.startswith(reg+', '+dest+' <')
        assert any(instructions[a][0]=='adrp' and instructions[a][1].startswith(args.split('[')[1].split(',')[0]+', 0x417000 <') for a in path)
        assert instructions[path[-2]]==('mov','w0, #-0x2') or name=='mfc_poll'
        depth=peak=0;proof=[]
        for i,address in enumerate(path):
            op,arg=instructions[address];proof.append({'address':hex(address),'instruction':op+' '+arg})
            assert op in ('adrp','add','ldr','orr','cbnz','mov','b','stp','ldp','ret')
            if op=='stp':
                assert '[sp,' in arg and op=='stp','Nonstack write on rejected path'
                if ']!' in arg:depth+=int(re.search(r'#-0x([0-9a-f]+)',arg)[1],16)
            if op=='ldp' and '[sp], #' in arg:depth-=int(re.search(r'\[sp\], #0x([0-9a-f]+)',arg)[1],16)
            peak=max(peak,depth);assert depth>=0
            if op=='b':assert int(re.search(r'0x([0-9a-f]+)',arg)[1],16)==path[i+1]
            if op=='cbnz':assert int(re.search(r'0x([0-9a-f]+)',arg)[1],16)==path[i+1]
        assert depth==0 and instructions[path[-1]][0]=='ret'
        assert any(instructions[a]==('mov','w0, #-0x2') for a in path)
        rejected[name]={'frame_bytes':peak,'active_condition':'mfc_active!=0 on entry; begin also ORs single-use started','instructions':proof,'calls':[],'nonstack_writes':False}
        frames[name+'[active]']=peak
    roots=['mfc_begin','mfc_poll','mfc_cancel','mfc_snapshot','read_reg','write_reg','fence','probe_reentry','aux_master_control_decode','aux_master_routing_ack_decode']
    rows=module('graph','inspect-caller-callgraph.py').inspect(text,frames,roots);nodes={}
    for row in rows.values():nodes.update(row['reachable_functions'])
    sites={0x401bc8:'fence',0x401c08:'read',0x401c8c:'write',0x401164:'decode',0x4011f0:'read',0x4012d8:'fence',0x401484:'write',0x4025a4:'read',0x402a58:'read',0x4032f0:'read',0x4015a4:'fence',0x401618:'read',0x401670:'write'}
    targets={'read':['read_reg'],'write':['write_reg'],'fence':['fence'],'decode':['aux_master_control_decode','aux_master_routing_ack_decode']}
    local={int(t['branch_address'],16) for t in helpers['computed_branches']};seen=set()
    for name,row in nodes.items():
        calls=set(row['calls'])|set(row['tail_branches'])
        # Only the deliberately reentrant probe runs with active=1. Replace
        # those edges by audited call-free rejection paths, not whole functions.
        if name=='probe_reentry':calls={n+'[active]' if n in rejected else n for n in calls}
        row['calls']=calls;row['frame_bytes']=frames.get(name,row['frame_bytes'])
        for site in row['indirect']:
            address=int(site['address'],16)
            if site['instruction'].startswith('br '):assert address in local;continue
            assert address in sites;seen.add(address);calls.update(targets[sites[address]])
        assert row['frame_bytes'] is not None,('Missing frame',name)
    assert seen==set(sites)
    for name,value in rejected.items():nodes[name+'[active]']={'calls':set(),'frame_bytes':value['frame_bytes']}
    def sum_path(name,trail=()):
        assert name not in trail,('Unresolved recursive cycle',trail,name)
        options=[sum_path(n,trail+(name,)) for n in nodes[name]['calls']]
        size,path=max(options,key=lambda x:x[0]) if options else (0,[])
        return nodes[name]['frame_bytes']+size,[name]+path
    sums={n:dict(zip(('bytes','path'),sum_path(n))) for n in roots[:4]}
    return {'status':'GUARDED_REENTRY_PATHS_AND_CONDITIONAL_DIAGNOSTIC_FRAME_SUM_PASS','rejected_entry_paths':rejected,'conditional_frame_sums':sums,'resolved_indirect_call_sites':len(seen),'local_jump_table_entries':31,'helper_frames':helpers['helpers'],'runtime_admitted':False,'hardware_accessed':False,'complete_production_stack_bound_bytes':None,'assumptions':['Exact frozen mock callbacks and two decoder targets; same sole foreground ownership contract','Only probe_reentry calls entry points from callbacks; guard remains nonzero throughout callback, as exercised by target tests','Compiler static frame metadata bounds per-function use; tail edges added conservatively'],'limits':['Diagnostic fixture adds probe112B plus rejectedpoll128B; not production stack budget','Outer caller, IRQ/nesting/FPU, activeEL/SP and integrated runtime omitted','No concurrency, panic-unwind, hardware worker handoff, recovery or clock qualification'],'input_sha256':{str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in [elf,base/'full-disassembly.txt',base/'stack-sizes.txt',base/'execution-results.json']+sorted(base.glob('codec-normal*.su'))}}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--artifacts',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=inspect(a.artifacts);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,indent=2)+'\n');print(r['status']);print(r['conditional_frame_sums'])
if __name__=='__main__':main()
