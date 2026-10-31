# SPDX-License-Identifier: LGPL-3.0-or-later
"""Host-only proposed fault-receipt codec, supplied snapshots not HW evidence."""
import struct
MAGIC=0x50465831

def encode(route,registers):
    if type(route) is not int or route not in (1,2):raise ValueError('known route required')
    if type(registers) is not dict or set(registers)-{'msr','esr','ear','edr'}:raise ValueError('known supplied registers only')
    words=[0]*16;words[:4]=[1,MAGIC,1,route]
    for i,name in enumerate(('msr','esr','ear','edr')):
        if name in registers:
            value=registers[name]
            if type(value) is not int or not 0<=value<2**32:raise ValueError('u32 snapshot required')
            words[4]|=1<<i;words[5+i]=value
    return struct.pack('<16I',*words)

def decode(data):
    if type(data) is not bytes or len(data)!=64:raise ValueError('exact immutable64 bytes required')
    w=struct.unpack('<16I',data)
    if w[:3]!=(1,MAGIC,1) or w[3] not in (1,2) or w[4]&~15:raise ValueError('unknown/incomplete fault record')
    if any(w[9:]):raise ValueError('reserved/session words must be zero')
    for i in range(4):
        if not(w[4]&(1<<i)) and w[5+i]:raise ValueError('invalid snapshot must be zero')
    return dict(kind='PROPOSED_FAULT_RECEIPT_NOT_NORMAL_TERMINAL',route=w[3],
        supplied_snapshots={n:w[5+i] for i,n in enumerate(('msr','esr','ear','edr')) if w[4]&(1<<i)},
        session_bound=False,hardware_executed=False,deployable=False,pmu_ram_access_allowed=False,
        sleep_proven=False,recovery_proven=False)
