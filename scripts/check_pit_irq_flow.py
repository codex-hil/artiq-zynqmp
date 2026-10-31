# SPDX-License-Identifier: LGPL-3.0-or-later
"""Exact scoped instruction pins for one reviewed MMIO LTO build, not generic flow proof."""
import hashlib,re
from package_local_candidate import loads
from check_pit_mailbox_layout import check as check_mailbox
from check_pit_word_stores import check as check_stores
PROFILE='pit-irq-bound-instruction-audit-v1'
PINS = {'barrier': (4292656980,
             60,
             '0fba4c40a943d76b54b37fa9de2f25fb9466d9c5bc338f0cba90dd388727ae54'),
 'disable': (4292656616,
             32,
             '4956afde32fea22016abd4ba0bbc742766d6194574e8820f1300a654b80e7515'),
 'fence': (4292657516,
           24,
           '24072df1489e3f1e888357098c23516e3112815901ea0796cee2303e250dcd30'),
 'microblaze_disable_interrupts': (4292661256,
                                   48,
                                   'd540a1070b31ec0c1490c729ea23529d0e6f0af5865698ce05604358dfe9b39c'),
 'observe': (4292656472,
             144,
             '5c0da7d5709806b74cb23f9c1dd11bb879a87af504caa1a10a9a80fd022eaf7c'),
 'pit_irq_composition_audit': (4292673656,
                               224,
                               'acac7c8022de2034ace1e3084086fa9f6a630291fb0b9eee114892f89770d805'),
 'pit_irq_disable_audit': (4292661304,
                           56,
                           'e44da0f4739d0d8e862da2edbbbe493dd545999e803493a4d90e4a8f9cb3abe2'),
 'pit_irq_msr_audit': (4292657732,
                       60,
                       '92d8217a83a377dc0674102f54408f786285c641c78d92c6466b0fd5e9d091be'),
 'pit_mailbox_composition_audit': (4292673176,
                                   480,
                                   '3fdeaab4f9a7c2e1072e59891145c4d603401e699d5e9c3de755229f01547f3c'),
 'pit_mailbox_sample_barrier_audit': (4292657636,
                                      48,
                                      '77d48e3ba52b2a12ab9550ea636229770671df458cf5cca3b70287a3e554de2d'),
 'pit_mailbox_sample_write_audit': (4292657540,
                                    48,
                                    '7c63c35540910f4d1907f77d93e76474bfd6204d1859de0b7335dde72625a56c'),
 'pit_mailbox_terminal_barrier_audit': (4292657684,
                                        48,
                                        '78125547d638e88dbff911c915df89a48f988c523cc3ab77c58e60d8edda2daf'),
 'pit_mailbox_terminal_write_audit': (4292657588,
                                      48,
                                      '68d15108f49a61bb45a54b1b71989a4355a320de0a58f210477cc8447b4b7f8c'),
 'pit_mmio_composition_audit': (4292671276,
                                1900,
                                'fe55f4923c2f0579055dffe74c5e862835a1265ce68bdbee994934626e6d3081'),
 'pit_mmio_read': (4292657048,
                   112,
                   '98677f3e59f558fc5ab4822e9675a3815c7b758eabfbbe901b8271ad842fc53b'),
 'pit_terminal_audit': (4292671264,
                        12,
                        'e7d88279bc84b61d056548cfcf38d58409152261590feb9ee5a4ca4891564efc'),
 'pit_word_slot_barrier': (4292657356,
                           160,
                           '40c3c8c2d65f13c3952f141ca4b3df27992c529a9e95c967547ebb493582224e'),
 'pit_word_slot_write': (4292657160,
                         196,
                         '691f1e0d3d7010960f2d4e5c9f62350eaeea6326a35db236858b66a6429b94a0'),
 'read_word': (4292656648,
               272,
               '3f636c1483eb42c9fa9e0f758153f818cc8eeab4a9da5ba61b08d91f7ba86a98'),
 'write_word': (4292656920,
                60,
                '97fb08fb93dc1a24a687758b1ad5dacab1ab9a957433e428c29608589863624d')}
STORAGE_PINS={'pit_mailbox_audit': (4292725504, 144, 'B'), 'sample_slot': (4292725432, 32, 'b'), 'terminal_slot': (4292725400, 32, 'b')}

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
            'functions':result,'owned_storage':STORAGE_PINS,'mailbox':mailbox,'external_callback_paths_qualified':False,'limits':'Exact twenty-function byte/range consistency for one reviewed owned-mailbox LTO artifact. Includes both linked IRQ helper paths and the configuration-read address, not live configuration contents. Vendor code elsewhere is outside scope. No generic CFG/dataflow, liveness, caller callback trust, physical origin, total stack, memory ownership or deployment proof.'}
