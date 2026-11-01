# SPDX-License-Identifier: LGPL-3.0-or-later
"""Abstract atomic-word publication model, not a physical exception simulator."""
import struct
from pit_exception_receipt import encode,decode

def events(record):
    words=struct.unpack('<16I',record)
    decode(record)
    return [('write',0,0),('fence',None,None)]+[('write',i,words[i]) for i in range(1,16)]+[('fence',None,None),('write',0,1)]
def apply(state,event):
    kind,index,value=event
    if kind=='write':state[index]=value
    elif kind!='fence':raise ValueError('unknown model event')
def classify(words,a,b):
    raw=struct.pack('<16I',*words)
    try:decode(raw)
    except ValueError:return 'rejected'
    return 'a' if raw==a else 'b' if raw==b else 'structurally_valid_mixed'
def analyze():
    a=encode(1,dict(msr=0x101,esr=0x102,ear=0x103))
    b=encode(2,dict(msr=0x201,esr=0x202,ear=0x203))
    ea,eb=events(a),events(b)
    single=[]
    for prefix in range(len(ea)+1):
        state=[0]*16
        for event in ea[:prefix]:apply(state,event)
        single.append(dict(prefix=prefix,result=classify(state,a,b)))
    # Faithful control-flow class: nested B is nonreturning, A cannot resume.
    nested=[]
    for cut in range(len(ea)+1):
        for prefix in range(len(eb)+1):
            state=[0]*16
            for event in ea[:cut]+eb[:prefix]:apply(state,event)
            nested.append(dict(outer_prefix=cut,inner_prefix=prefix,result=classify(state,a,b)))
    # Deliberately forbidden class: outer resumes after inner. Counterexamples
    # show why ownership/nonreturn assumptions cannot be dropped. Not prediction
    # of a single-core nested nonreturning handler or hardware reachability.
    resumed=[];witness=None
    for cut in range(len(ea)+1):
        state=[0]*16
        trace=[('a',e) for e in ea[:cut]]+[('b',e) for e in eb]+[('a',e) for e in ea[cut:]]
        for owner,event in trace:apply(state,event)
        result=classify(state,a,b);resumed.append(dict(cut=cut,result=result))
        if result=='structurally_valid_mixed' and witness is None and state[5]==0x201 and state[6]==0x102:
            witness=dict(cut=cut,trace=[dict(owner=o,kind=e[0],word=e[1],value=e[2]) for o,e in trace],final_hex=struct.pack('<16I',*state).hex(),decoded=decode(struct.pack('<16I',*state)))
    counts=lambda rows:{kind:sum(r['result']==kind for r in rows) for kind in ['rejected','a','b','structurally_valid_mixed']}
    return dict(status='ABSTRACT_WORD_MODEL_NOT_PHYSICAL_EXCEPTION_PROOF',hardware_executed=False,deployable=False,
        assumptions=['Atomic in-order u32 stores and completed fences; no memory/bus faults, reordering or timing.','Nested inner never returns: outer cannot resume in faithful class.','Reads here are abstract snapshots, not permission to access PMU RAM.'],
        record_a_hex=a.hex(),record_b_hex=b.hex(),events_per_writer=len(ea),
        single_prefixes=single,nested_nonreturning_counts=counts(nested),nested_nonreturning_cases=len(nested),
        forbidden_outer_resume_counts=counts(resumed),forbidden_outer_resume_cases=len(resumed),mixed_witness=witness,
        first_fault_preserved=False,session_bound=False,reentry_excluded=False,pmu_ram_access_allowed=False,
        limits='Exhaustive bounded prefix/contiguous-insertion classes only, not all interleavings or physical reachability. Structural decode cannot establish identity, first-fault preservation, sleep or recovery.')
