#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Conservative bit-skew enumeration, not a metastability simulator."""
import ast
import hashlib
import itertools
import json
from pathlib import Path

SOURCE = Path('/srv/codex-hil-data/artiq-zynqmp/work/kasli-master/artiq/gateware/drtio/aux_controller.py')

def mixed_values(old, new, width=3):
    return sorted({sum((((new if choose else old) >> bit) & 1) << bit
                       for bit, choose in enumerate(selection))
                   for selection in itertools.product((False, True), repeat=width)})

def review():
    text = SOURCE.read_text()
    tree = ast.parse(text)
    receiver = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'Receiver')
    crossings = [n for n in ast.walk(receiver) if isinstance(n, ast.Call)
                 and isinstance(n.func, ast.Name) and n.func.id == 'MultiReg']
    pairs = [(n.args[0].id, n.args[1].id) for n in crossings]
    assert sorted(pairs) == [('read_pointer', 'read_pointer_rx'), ('write_pointer', 'write_pointer_sys')]
    binary = []
    gray = []
    for old in range(8):
        new = (old + 1) % 8
        mixed = mixed_values(old, new)
        binary.append({'old': old, 'new': new, 'possible_bitwise_samples': mixed,
                       'non_endpoint_samples': [v for v in mixed if v not in (old, new)]})
        a, b = old ^ (old >> 1), new ^ (new >> 1)
        assert set(mixed_values(a, b)) == {a, b}
        gray.append({'old_encoded': a, 'new_encoded': b})
    assert len(binary[3]['non_endpoint_samples']) == 6
    return {'status': 'NATIVE_BINARY_POINTER_ATOMICITY_NOT_QUALIFIED',
            'source_sha256': hashlib.sha256(text.encode()).hexdigest(),
            'source': str(SOURCE), 'direct_multireg_pairs': pairs,
            'binary_increment_enumeration': binary, 'gray_increment_reference': gray,
            'counterexample': {'transition': '3 -> 4', 'mixed_sample': 0,
                'consumer_pointer': 0,
                'implication': 'Equality can indicate empty although neither stable producer pointer equals consumer pointer'},
            'limits': ['Conservative bit-skew possibility, not observed hardware failure or probability',
                      'Gray reference alone is not an implementation fix; registered encoding, decoding, timing bounds and reset ownership need review',
                      'Packet SRAM visibility and full-ring producer protection need separate proof'],
            'required_reset_contract': ['Coordinate master/control and rtio_rx reset with link admission disabled',
                'Clear both pointers and synchronizer pipelines before admitting new packets',
                'Do not assume resetting the PS AXI bridge resets native AUX receiver',
                'Qualify stopped recovered clock and subsequent reset release before hardware'],
            'hardware_accessed': False}

if __name__ == '__main__':
    print(json.dumps(review(), indent=2))
