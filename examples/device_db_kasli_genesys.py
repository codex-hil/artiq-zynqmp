"""Direct Kasli master / Genesys destination1 laboratory leaf; LGPL-3.0-or-later.

Requires the qualified SRAM runtime/leaf session. The combined test restores
both boards afterward; this database alone does not load their images.
Update the scoped host address/interface if the master or host NIC changes.
"""
device_db = {
    'core': {'type':'local', 'module':'artiq.coredevice.core', 'class':'Core',
             'arguments': {'host':'fe80::4b:3ff:fe48:4854%enp2s0',
                           'target':'rv32ima', 'ref_period':1e-9,
                           'analyzer_proxy':None}},
    'ttl_out': {'type':'local', 'module':'artiq.coredevice.ttl', 'class':'TTLOut',
                'arguments': {'channel':0x10000}},
    'ttl_in': {'type':'local', 'module':'artiq.coredevice.ttl', 'class':'TTLInOut',
               'arguments': {'channel':0x10001}},
}
