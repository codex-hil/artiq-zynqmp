# SPDX-License-Identifier: LGPL-3.0-or-later
"""Exact scoped instruction pins for one reviewed MMIO LTO build, not generic flow proof."""
import hashlib,re
from package_local_candidate import loads
from check_pit_mailbox_layout import check as check_mailbox
from check_pit_word_stores import check as check_stores
PROFILE='pit-digest-root-instruction-audit-v1'
PINS = {'barrier.lto_priv.1': (4292659904,
                        60,
                        'a7483316d3c4a508b6e2b314703ebfae2175aa1e8bb36467e563c2cb8d46be36'),
 'digest_ordered_read': (4292659972,
                         48,
                         '4ead6bbbac189cb2984e1f4aa5661a935b13a01314bd33b29fae08fb787d4ea5'),
 'disable.lto_priv.1': (4292659744,
                        32,
                        '4956afde32fea22016abd4ba0bbc742766d6194574e8820f1300a654b80e7515'),
 'microblaze_disable_interrupts': (4292663796,
                                   48,
                                   '4bbeffebe8b8c494ec9b73c6ac6a1bd69ddd7aff9ed68ef9831558476a8f23e8'),
 'observe.lto_priv.1': (4292659600,
                        144,
                        '1f91aac045343610a02c3e53663c8ad58f76308453bb0f8e4e792f38e0ad5409'),
 'pit_capture_digest': (4292676060,
                        448,
                        'f3490161d7565ed0f0ef1fdf044da05adda35664c73f5baff273dead13474a8d'),
 'pit_collect.constprop.0': (4292660020,
                             312,
                             '66e456c6b8eb4be8cc34e800346932916a210bebd588b45a71ff8195a830a7c8'),
 'pit_digest_root_audit': (4292676508,
                           1500,
                           '463c1af060ddb34369e0ff0e3c55e5ff745d5d381bbadf10563330cc4365b8aa'),
 'pit_irq_composition_audit': (4292674880,
                               224,
                               '74c27d0565ade610612f79c33c851dd4868af62cebbe3ccbae41e20990e5b4d2'),
 'pit_irq_disable_audit': (4292663844,
                           56,
                           'e44da0f4739d0d8e862da2edbbbe493dd545999e803493a4d90e4a8f9cb3abe2'),
 'pit_irq_msr_audit': (4292659528,
                       60,
                       '92d8217a83a377dc0674102f54408f786285c641c78d92c6466b0fd5e9d091be'),
 'pit_mailbox_composition_audit': (4292674608,
                                   272,
                                   '130e6e45d2cf5bc99807454265a4b452ecd5ddb59df02b36f53b529730b8b584'),
 'pit_mailbox_prepare_audit': (4292659088,
                               248,
                               'f3710042b28834439cc80972949d3fe2c194569a3f11729f1d7066519fc14281'),
 'pit_mailbox_sample_barrier_audit': (4292659432,
                                      48,
                                      '219b53f5eb2e63abab6dac3cff83a428509d6709c7ebd2b839a1a165fd7343e5'),
 'pit_mailbox_sample_write_audit': (4292659336,
                                    48,
                                    '45128e223d7e6dcd0785a842e1914d30e6852cb3eb72dedba8d9ccb708bf6dbc'),
 'pit_mailbox_terminal_barrier_audit': (4292659480,
                                        48,
                                        'c105a6d6634b28574a72a29e0664b48ee7131455e0544afc0ccd10f9765c2a63'),
 'pit_mailbox_terminal_write_audit': (4292659384,
                                      48,
                                      '884b3a947218d8ccdb6771055b1e4358d4b893424dfbab4fdf3ceb71cd0509ca'),
 'pit_mmio_read': (4292658596,
                   112,
                   '98677f3e59f558fc5ab4822e9675a3815c7b758eabfbbe901b8271ad842fc53b'),
 'pit_publish': (4292656472,
                 404,
                 '6f75d115c4ecafa004c189498e627c247be385ac4ee650d4e7f08465a7a60de6'),
 'pit_ro_read': (4292658304,
                 200,
                 '0d9e5f89ce9718980de7425f74cf9665be01a61a5af8003d1eebdc3e70a50d90'),
 'pit_sample_sha256': (4292675104,
                       956,
                       'ae451d029b4ec0960045ad8f3d92be58cc5f8ca33131253e4040fe8a903cb470'),
 'pit_terminal_audit': (4292673804,
                        12,
                        'e7d88279bc84b61d056548cfcf38d58409152261590feb9ee5a4ca4891564efc'),
 'pit_terminal_build': (4292657444,
                        556,
                        'f394175e25e4b9d09f4e829206cf7e77683040062aeca956d088f481005a8845'),
 'pit_terminal_publish': (4292656876,
                          568,
                          '7ecb8be8bf90e318ce23b4ea62e5685cec21854dc8b1002b65e47eeb6d30757d'),
 'pit_word_slot_barrier': (4292658904,
                           160,
                           '40c3c8c2d65f13c3952f141ca4b3df27992c529a9e95c967547ebb493582224e'),
 'pit_word_slot_write': (4292658708,
                         196,
                         '691f1e0d3d7010960f2d4e5c9f62350eaeea6326a35db236858b66a6429b94a0'),
 'read_word.lto_priv.1': (4292659776,
                          68,
                          'b1e00c5dff13c8109ed5396ec37b36f731b28f7f269b4198ebe82a45254ac0aa'),
 'swap': (4292659588,
          12,
          '0f2fbab8208005634f344ae010072b66d3f4312d025863658592d6d779659618'),
 'write_word.lto_priv.1': (4292659844,
                           60,
                           'f48080dd1ba8faa60981d533f2c8252711c51009294ad2d3398ba8f193acb115')}
STORAGE_PINS={'pit_mailbox_audit': (4292729912, 144, 'B'), 'sample_slot': (4292729840, 32, 'b'), 'terminal_slot': (4292729808, 32, 'b'), 'digest_read_adapter': (4292729784, 24, 'b')}
CONSTANT_PIN=(4292695848, 256, '74ef7306e7452d6859b6463ce496b8df30925f69e1b2969e1f3f34bbc9c6af04')

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
    constant_rows=re.findall(r'^([0-9a-f]+) ([0-9a-f]+) r k$',symbols_text,re.M)
    a,z,h=CONSTANT_PIN
    if constant_rows!=[(f'{a:08x}',f'{z:08x}')]:raise ValueError('changed SHA constant range')
    spans=[s for s in segments if s['address']<=a and a+z<=s['address']+s['filesz']]
    if len(spans)!=1:raise ValueError('SHA constants not uniquely file backed')
    seg=spans[0];constants=seg['payload'][a-seg['address']:a-seg['address']+z]
    if hashlib.sha256(constants).hexdigest()!=h:raise ValueError('changed SHA constants')
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
            'functions':result,'owned_storage':STORAGE_PINS,'mailbox':mailbox,'external_callback_paths_qualified':False,'limits':'Exact scoped digest-root byte/range consistency for one reviewed owned-mailbox LTO artifact. Includes SHA constants and both linked IRQ helper paths/configuration-read address, not live configuration contents. Vendor code elsewhere is outside scope. No generic CFG/dataflow, liveness, caller callback trust, physical origin, total stack, memory ownership or deployment proof.'}
