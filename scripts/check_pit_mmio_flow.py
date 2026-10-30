# SPDX-License-Identifier: LGPL-3.0-or-later
"""Exact scoped instruction pins for one reviewed MMIO LTO build, not generic flow proof."""
import hashlib,re
from package_local_candidate import loads
from check_pit_word_stores import check as check_stores
PROFILE='pit-concrete-mmio-instruction-audit-v1'
PINS = {'pit_mmio_composition_audit': (4292670564, 1880, '1efb053e1ae486b736db661ab908a06aced3dbb7c006d7fa597ab1e765f8c0f0'), 'pit_mmio_read': (4292657072, 112, '98677f3e59f558fc5ab4822e9675a3815c7b758eabfbbe901b8271ad842fc53b'), 'pit_terminal_audit': (4292670552, 12, 'e7d88279bc84b61d056548cfcf38d58409152261590feb9ee5a4ca4891564efc'), 'observe': (4292656496, 144, '5c0da7d5709806b74cb23f9c1dd11bb879a87af504caa1a10a9a80fd022eaf7c'), 'disable': (4292656640, 32, '4956afde32fea22016abd4ba0bbc742766d6194574e8820f1300a654b80e7515'), 'read_word': (4292656672, 272, '3f636c1483eb42c9fa9e0f758153f818cc8eeab4a9da5ba61b08d91f7ba86a98'), 'write_word': (4292656944, 60, '97fb08fb93dc1a24a687758b1ad5dacab1ab9a957433e428c29608589863624d'), 'barrier': (4292657004, 60, '0fba4c40a943d76b54b37fa9de2f25fb9466d9c5bc338f0cba90dd388727ae54'), 'memset': (4292683736, 276, 'eedfca5b425b9c8c5403a73fe6e7b81bf390ea99cb00e5eb7399568cfa957ed5')}

def check(data,symbols_text,disassembly):
    machine,entry,segments=loads(data)
    if machine!=189 or entry!=0xffdc0050:raise ValueError('full MicroBlaze audit ELF required')
    symbols={}
    for line in symbols_text.splitlines():
        match=re.fullmatch(r'([0-9a-f]+) ([0-9a-f]+) [tT] (\S+)',line)
        if match:
            if match[3] in symbols:raise ValueError('duplicate function symbol')
            symbols[match[3]]=(int(match[1],16),int(match[2],16))
    rows={}
    for line in disassembly.splitlines():
        match=re.fullmatch(r'\s*([0-9a-f]+):\s+([0-9a-f]{8})\s+.+',line)
        if match:
            pc=int(match[1],16)
            if pc in rows:raise ValueError('duplicate disassembly instruction')
            rows[pc]=int(match[2],16)
    result={}
    for name,(start,size,digest) in PINS.items():
        if symbols.get(name)!=(start,size):raise ValueError('unexpected function range: '+name)
        body=bytearray()
        for pc in range(start,start+size,4):
            matches=[s for s in segments if s['address']<=pc and pc+4<=s['address']+s['filesz']]
            if len(matches)!=1:raise ValueError('instruction outside unique load range')
            seg=matches[0];word=seg['payload'][pc-seg['address']:pc-seg['address']+4]
            if rows.get(pc)!=int.from_bytes(word,'little'):raise ValueError('stale/missing disassembly')
            body.extend(word)
        if hashlib.sha256(body).hexdigest()!=digest:raise ValueError('changed reviewed instructions: '+name)
        # Library byte paths remain a separately reported unclosed obligation.
        # Pinning their bytes cannot establish effective call arguments/alignment.
        stores = check_stores(data,symbols_text,name) if name!='memset' else {
            'status':'LIBRARY_SUBWORD_PATHS_PRESENT_NOT_QUALIFIED',
            'qualification_complete':False}
        result[name]={'instruction_words':size//4,'sha256':digest,'stores':stores}
    return {'status':'EXACT_SCOPED_MMIO_INSTRUCTION_PINS_PASS_NOT_DEPLOYMENT','profile':PROFILE,
            'hardware_executed':False,'deployable':False,'destructive_test_allowed':False,
            'functions':result,'library_store_width_qualified':False,'limits':'Exact nine-function byte/range consistency for one reviewed LTO artifact. No generic CFG/dataflow, liveness, caller callback trust, physical origin, total stack, memory ownership or deployment proof.'}
