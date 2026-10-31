# SPDX-License-Identifier: LGPL-3.0-or-later
"""Exact scoped instruction pins for one reviewed MMIO LTO build, not generic flow proof."""
import hashlib,re
from package_local_candidate import loads
from check_pit_mailbox_layout import check as check_mailbox
from check_pit_word_stores import check as check_stores
PROFILE='pit-owned-mailbox-instruction-audit-v1'
PINS = {'barrier': (4292657004,
             60,
             '0fba4c40a943d76b54b37fa9de2f25fb9466d9c5bc338f0cba90dd388727ae54'),
 'disable': (4292656640,
             32,
             '4956afde32fea22016abd4ba0bbc742766d6194574e8820f1300a654b80e7515'),
 'fence': (4292657540,
           24,
           '24072df1489e3f1e888357098c23516e3112815901ea0796cee2303e250dcd30'),
 'observe': (4292656496,
             144,
             '5c0da7d5709806b74cb23f9c1dd11bb879a87af504caa1a10a9a80fd022eaf7c'),
 'pit_mailbox_composition_audit': (4292673036,
                                   480,
                                   'f632c0f4e7c0d255e49c8950b02cc678d667a3f6621691979fbe5781d5130378'),
 'pit_mailbox_sample_barrier_audit': (4292657660,
                                      48,
                                      '034066ca48f1d81dae1f8fab8503aed9e13756f77b6d69bf78e7306cfb50ace7'),
 'pit_mailbox_sample_write_audit': (4292657564,
                                    48,
                                    'b55c18323dcd42e1ae611f03cd9e7e847279b66c5c53133268a78fc3364cf298'),
 'pit_mailbox_terminal_barrier_audit': (4292657708,
                                        48,
                                        'b7d085877bed6c0c0aac6a03974ba92f8ac9b959c93a896130761c78b583fcaa'),
 'pit_mailbox_terminal_write_audit': (4292657612,
                                      48,
                                      '2738e75c09e6d1a81e3cf5c5eea87fac960dde1e9dc0bb32dbb7ba319d233131'),
 'pit_mmio_composition_audit': (4292671136,
                                1900,
                                '4396a38d2cebeadf491a5f7306f717f4cf3180c69d423b9f270827989659568f'),
 'pit_mmio_read': (4292657072,
                   112,
                   '98677f3e59f558fc5ab4822e9675a3815c7b758eabfbbe901b8271ad842fc53b'),
 'pit_terminal_audit': (4292671124,
                        12,
                        'e7d88279bc84b61d056548cfcf38d58409152261590feb9ee5a4ca4891564efc'),
 'pit_word_slot_barrier': (4292657380,
                           160,
                           '40c3c8c2d65f13c3952f141ca4b3df27992c529a9e95c967547ebb493582224e'),
 'pit_word_slot_write': (4292657184,
                         196,
                         '691f1e0d3d7010960f2d4e5c9f62350eaeea6326a35db236858b66a6429b94a0'),
 'read_word': (4292656672,
               272,
               '3f636c1483eb42c9fa9e0f758153f818cc8eeab4a9da5ba61b08d91f7ba86a98'),
 'write_word': (4292656944,
                60,
                '97fb08fb93dc1a24a687758b1ad5dacab1ab9a957433e428c29608589863624d')}
STORAGE_PINS={'pit_mailbox_audit':(0xffddc980,144,'B'),'sample_slot':(0xffddc938,32,'b'),'terminal_slot':(0xffddc918,32,'b')}

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
    storage={}
    for line in symbols_text.splitlines():
        match=re.fullmatch(r'([0-9a-f]+) ([0-9a-f]+) ([bB]) (\S+)',line)
        if match:
            if match[4] in storage:raise ValueError('duplicate storage symbol')
            storage[match[4]]=(int(match[1],16),int(match[2],16),match[3])
    for name,bounds in STORAGE_PINS.items():
        if storage.get(name)!=bounds:raise ValueError('changed owned storage: '+name)
    mailbox=check_mailbox(data,symbols_text)
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
        stores = check_stores(data,symbols_text,name)
        result[name]={'instruction_words':size//4,'sha256':digest,'stores':stores}
    return {'status':'EXACT_SCOPED_MMIO_INSTRUCTION_PINS_PASS_NOT_DEPLOYMENT','profile':PROFILE,
            'hardware_executed':False,'deployable':False,'destructive_test_allowed':False,
            'functions':result,'owned_storage':STORAGE_PINS,'mailbox':mailbox,'external_callback_paths_qualified':False,'limits':'Exact sixteen-project-function byte/range consistency for one reviewed owned-mailbox LTO artifact. Vendor library code elsewhere is outside scope. No generic CFG/dataflow, liveness, caller callback trust, physical origin, total stack, memory ownership or deployment proof.'}
