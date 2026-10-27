"""Offline receipt framing for the C PIT record. LGPL-3.0-or-later.

No physical reader/barrier/atomicity guarantee. Stable stale bytes and ABA are
not excluded by double sampling; lifetime/visibility must be established outside.
"""
import struct
from pit_counter_observation import ADDRESSES, decode, _uint

SIZE = 48


def accept(first, second, expected_nonce):
    """Accept two caller-supplied exact byte snapshots, never a HW permit."""
    _uint(expected_nonce, 64, True)
    if type(first) is not bytes or type(second) is not bytes:
        raise ValueError('immutable bytes required')
    if len(first) != SIZE or len(second) != SIZE:
        raise ValueError('exact 48-byte snapshots required')
    if first != second:
        raise ValueError('publication changed between snapshots')
    complete, version, nonce, *values = struct.unpack('<IIQ8I', first)
    if complete != 1:
        raise ValueError('record not committed')
    observation = decode({'version': version, 'nonce': nonce, 'samples': [
        {'sequence': i, 'address': ADDRESSES[i % 4], 'value': value}
        for i, value in enumerate(values)]}, expected_nonce)
    observation['publication'] = 'Two equal supplied snapshots only; visibility/lifetime unqualified'
    return observation
