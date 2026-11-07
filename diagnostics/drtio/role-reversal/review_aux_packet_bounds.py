#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Review pinned native RX word/byte bound; no RTL or hardware mutation."""
import ast
import hashlib
import json
from pathlib import Path
from migen import bits_for, log2_int

SOURCE = Path('/srv/codex-hil-data/artiq-zynqmp/work/kasli-master/artiq/gateware/drtio/aux_controller.py')

def review():
    source = SOURCE.read_text()
    tree = ast.parse(source)
    constants = {n.targets[0].id: ast.literal_eval(n.value) for n in tree.body
                 if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name)}
    receiver = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'Receiver')
    comparisons = [n for n in ast.walk(receiver) if isinstance(n, ast.Compare)
                   and isinstance(n.left, ast.Name) and n.left.id == 'frame_counter']
    assert any(ast.unparse(n) == 'frame_counter == max_packet' for n in comparisons)
    # Pin reviewed width/address expressions instead of assuming changed source.
    for expression in ('bits_for(max_packet) - log2_int(mem_dw // 8)',
                       'frame_counter_nbits - 1', 'frame_counter + 1'):
        assert any(ast.unparse(n) == expression for n in ast.walk(receiver))
    maximum = constants['max_packet']
    width = bits_for(maximum) - log2_int(32//8)
    address_width = width-1
    assert maximum == 1024 and width == 9 and address_width == 8
    return {'status': 'STATIC_NATIVE_RX_LENGTH_BOUND_UNREACHABLE_FOR_DW32',
            'source': str(SOURCE), 'source_sha256': hashlib.sha256(source.encode()).hexdigest(),
            'configuration': {'link_aux_bits': 4, 'memory_word_bits': 32,
                              'max_packet_bytes': maximum, 'words_per_slot': maximum//4},
            'counter': {'unit': 'converter output words', 'bits': width,
                        'max_representable': (1<<width)-1,
                        'native_comparison': 'frame_counter == max_packet (1024)',
                        'comparison_reachable': False,
                        'slot_address_bits': address_width,
                        'word_index_256_address': 256 & ((1<<address_width)-1)},
            'publication_review': ['SRAM writes precede SIGNAL_FRAME pointer publication',
                'Full ring discards current uncommitted slot by withholding pointer advance',
                'Payload address uses low8 word-counter bits, so word256 aliases slot offset0',
                'EOP transition follows length-error transition in FRAME; overlay must define precedence explicitly'],
            'next_dynamic_cases': ['1020 byte packet', '1024 byte packet',
                '1028 byte packet rejected without publication',
                'EOP at offending word', 'Malformed oversized frame followed by valid packet',
                'Full ring preserves all previously published slots'],
            'limits': ['Static source/width analysis only; no malformed-frame simulation yet',
                       'No claim that current normal transmit firmware emits oversized frames',
                       'No upstream source modification or native AUX overlay adoption'],
            'hardware_accessed': False}

if __name__ == '__main__':
    print(json.dumps(review(), indent=2))
