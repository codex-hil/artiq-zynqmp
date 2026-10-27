"""Exact standalone audit ELF loop check, never deployment. LGPL-3.0-or-later."""
import struct
from package_local_candidate import loads


def check(data):
    machine, entry, segments = loads(data)
    if machine != 189 or entry != 0 or len(segments) != 1:
        raise ValueError('expected standalone MicroBlaze audit ELF at zero')
    segment = segments[0]
    if segment['address'] != 0 or segment['vaddr'] != 0 or segment['filesz'] != 12:
        raise ValueError('unexpected audit code region')
    words = struct.unpack('<3I', segment['payload'])
    if words != (0xb8220004, 0xba020004, 0xb800fffc):
        raise ValueError('expected mbar1/sleep/branch-back-to-sleep only')
    return {'status': 'STANDALONE_TERMINAL_FLOW_PASS_NOT_HARDWARE',
            'hardware_executed': False, 'deployable': False,
            'physical_backend_ready': False, 'destructive_test_allowed': False,
            'instruction_bytes': 12, 'entry': 0, 'sleep_pc': 4,
            'limits': 'Static three-instruction loop only; no PMU image, live MSR, sleep residency or visibility proof'}
