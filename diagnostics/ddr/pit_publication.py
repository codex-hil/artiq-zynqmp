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


class OfflinePublisher:
    """One-shot sequential callback model; no physical addresses or MMIO.

    write(offset, u32) and barrier() return None or raise. Exceptions leave
    visibility UNKNOWN, including a possibly completed commit. No retry/clear.
    Caller owns the slot and must supply a never-reused nonce/lifetime externally.
    A fresh instance does not prove freshness. Not thread-safe or reset-persistent.
    """
    def __init__(self):
        self._consumed = False

    def publish(self, record, nonce, write, barrier):
        accept(record, record, nonce)  # Validate private completed source first.
        if not callable(write) or not callable(barrier):
            raise ValueError('write and barrier callbacks required')
        if self._consumed:
            raise ValueError('publisher already consumed')
        self._consumed = True
        words = struct.unpack('<12I', record)
        attempted = 0
        try:
            attempted += 1
            write(0, 0)
            attempted += 1
            barrier()  # Invalidation must precede visible payload replacement.
            for index in range(1, 12):
                attempted += 1
                write(index * 4, words[index])
            attempted += 1
            barrier()  # Payload must precede the commit.
            attempted += 1
            write(0, 1)
        except Exception:
            return {'status': 'VISIBILITY_UNKNOWN', 'attempted_callbacks': attempted,
                    'physical_backend_ready': False, 'destructive_test_allowed': False}
        return {'status': 'CALLBACKS_RETURNED_OFFLINE', 'attempted_callbacks': attempted,
                'physical_backend_ready': False, 'destructive_test_allowed': False}
