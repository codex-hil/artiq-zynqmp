"""Reject subword stores in one linked PIT function. LGPL-3.0-or-later."""
import re
import struct
from package_local_candidate import loads


def check(data, symbols, name='pit_profile_entry_audit'):
    machine, entry, segments = loads(data)
    if machine != 189:
        raise ValueError('MicroBlaze ELF required')
    matches = re.findall(r'^([0-9a-f]+) ([0-9a-f]+) [tT] ' + re.escape(name) + r'$', symbols, re.M)
    if len(matches) != 1:
        raise ValueError('unique sized function required')
    start, size = (int(n, 16) for n in matches[0])
    if not size or size % 4 or start % 4:
        raise ValueError('unaligned function')
    count = 0
    for pc in range(start, start + size, 4):
        spans = [s for s in segments if s['address'] <= pc and pc + 4 <= s['address'] + s['filesz']]
        if len(spans) != 1:
            raise ValueError('function not in unique file-backed ELF range')
        segment = spans[0]
        word = struct.unpack_from('<I', segment['payload'], pc - segment['address'])[0]
        opcode = word & 0xfc000000
        if opcode in (0xd0000000, 0xd4000000, 0xf0000000, 0xf4000000):
            raise ValueError('PMU RAM subword store at ' + hex(pc))
        if opcode in (0xd8000000, 0xf8000000):
            count += 1
    return {'status': 'SCOPED_NO_SUBWORD_STORE_PASS_NOT_HARDWARE', 'word_store_sites': count,
            'hardware_executed': False, 'deployable': False, 'destructive_test_allowed': False,
            'limits': 'Opcode inventory only; alignment, callback/library/exception paths and device behavior need separate proof'}
