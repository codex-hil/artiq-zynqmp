# SPDX-License-Identifier: LGPL-3.0-or-later
"""Image-owned mailbox allocation only, never permission to access PMU RAM."""
import hashlib,re
from package_local_candidate import loads
from check_pmu_boundary_image import check as check_layout

def check(data,text):
    baseline=check_layout(data,text)
    symbols={}
    for line in text.splitlines():
        match=re.fullmatch(r'([0-9a-fA-F]+) (?:([0-9a-fA-F]+) )?([a-zA-Z]) (\S+)',line)
        if match:
            if match[4] in symbols:raise ValueError('duplicate symbol')
            symbols[match[4]]=(int(match[1],16),int(match[2],16) if match[2] else 0,match[3])
    mailbox=symbols.get('pit_mailbox_audit')
    if not mailbox or mailbox[1]!=144 or mailbox[2] not in 'bB' or mailbox[0]%8:
        raise ValueError('one aligned144-byte BSS mailbox required')
    start=mailbox[0];end=start+144
    required=['__bss_start','__bss_end','_stack_end','_stack','artiq_pmu_boundary']
    if not all(name in symbols for name in required):raise ValueError('missing ownership boundaries')
    bss_start=symbols['__bss_start'][0];bss_end=symbols['__bss_end'][0]
    stack_start=symbols['_stack_end'][0];stack_end=symbols['_stack'][0]
    if not bss_start<=start<end<=bss_end<=stack_start<stack_end:
        raise ValueError('mailbox outside BSS or overlaps stack')
    for name,(a,n,kind) in symbols.items():
        if name!='pit_mailbox_audit' and n and kind in 'bBdDsS' and start<a+n and a<end:
            raise ValueError('mailbox overlaps sized storage symbol: '+name)
    _,_,segments=loads(data)
    spans=[s for s in segments if s['address']+s['filesz']<=start and end<=s['address']+s['memsz']]
    if len(spans)!=1 or not spans[0]['flags']&2:raise ValueError('mailbox not unique writable zero-init load memory')
    heap_names=('_heap_start','_heap_end')
    heap_present=[n in symbols for n in heap_names]
    if any(heap_present) and not all(heap_present):raise ValueError('incomplete heap bounds')
    heap='NO_HEAP_BOUNDS_SYMBOLS_DYNAMIC_HEAP_NOT_EXCLUDED'
    if all(heap_present):
        lo,hi=(symbols[n][0] for n in heap_names)
        if lo>hi or (lo<hi and start<hi and lo<end):raise ValueError('invalid/overlapping heap bounds')
        heap='SYMBOL_BOUNDED_HEAP_DISJOINT_ONLY'
    return {'status':'MAILBOX_STATIC_ALLOCATION_PASS_NOT_CONSUMER_ADMISSION','hardware_executed':False,
            'deployable':False,'pmu_ram_access_allowed':False,'image_sha256':hashlib.sha256(data).hexdigest(),
            'mailbox':{'start':hex(start),'bytes':144,'end_exclusive':hex(end)},
            'samples':{'start':hex(start),'bytes':48},'terminal':{'start':hex(start+48),'bytes':96},
            'heap_scope':heap,'baseline_layout':baseline,
            'limits':'ELF/symbol allocation consistency only; zero-init segment is a loader obligation, not observed initialization. Dynamic allocation, callbacks, runtime lifetime, no-wake interval, authenticity and consumer/recovery remain unqualified.'}
