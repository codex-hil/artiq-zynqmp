"""Offline interpretation of PMU-local RO counter records. LGPL-3.0-or-later.

No capture backend: records are supplied by the caller, not authenticated.
Two sequential rounds are not atomic and establish no timer configuration.
"""
ADDRESSES = tuple(0xffd40044 + 0x10 * i for i in range(4))


def _uint(value, bits, nonzero=False):
    if type(value) is not int or not (int(nonzero) <= value < 1 << bits):
        raise ValueError('invalid unsigned integer')
    return value


def decode(record, expected_nonce):
    """Validate eight ordered observations; report equality only, never time."""
    _uint(expected_nonce, 64, True)
    if type(record) is not dict or set(record) != {'version', 'nonce', 'samples'}:
        raise ValueError('unexpected record fields')
    if type(record['version']) is not int or record['version'] != 1:
        raise ValueError('unsupported version')
    if _uint(record['nonce'], 64, True) != expected_nonce:
        raise ValueError('nonce mismatch')
    samples = record['samples']
    if type(samples) is not list or len(samples) != 8:
        raise ValueError('exactly two complete rounds required')
    for sequence, sample in enumerate(samples):
        if type(sample) is not dict or set(sample) != {'sequence', 'address', 'value'}:
            raise ValueError('unexpected sample fields')
        if _uint(sample['sequence'], 32) != sequence:
            raise ValueError('sample order mismatch')
        if _uint(sample['address'], 32) != ADDRESSES[sequence % 4]:
            raise ValueError('only ordered PIT0..3 RO counters allowed')
        _uint(sample['value'], 32)
    return {
        'scope': 'Untrusted supplied observations; no hardware execution established',
        'counters': [
            {'name': f'PIT{i}_COUNTER', 'address': ADDRESSES[i],
             'first': samples[i]['value'], 'second': samples[i + 4]['value'],
             'changed': samples[i]['value'] != samples[i + 4]['value']}
            for i in range(4)
        ],
        'elapsed_ticks': None, 'rollover_count': None,
        'frequency_hz': None, 'ownership': 'UNKNOWN',
        'physical_backend_ready': False, 'destructive_test_allowed': False,
    }
