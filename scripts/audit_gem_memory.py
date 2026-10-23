#!/usr/bin/env python3
"""Offline linked GEM memory audit, not DMA ownership; LGPL-3.0-or-later."""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

REQUIRED = ('emac_bd_space', 'tx_pbufs_storage', 'rx_pbufs_storage',
            'memp_memory_PBUF_POOL_base', 'ram_heap')


def symbols(text):
    found = {}
    for line in text.splitlines():
        m = re.fullmatch(r'([0-9a-fA-F]+) ([0-9a-fA-F]+) ([A-Za-z]) (\S+)', line)
        if not m or m[4] not in REQUIRED:
            continue
        if m[4] in found:
            raise ValueError('Duplicate symbol ' + m[4])
        start, size = int(m[1], 16), int(m[2], 16)
        if size <= 0 or start + size > 0x80000000 or m[3] not in 'Bb':
            raise ValueError('Unexpected low-DDR BSS allocation ' + m[4])
        found[m[4]] = dict(start=start, size=size, end_exclusive=start + size)
    if set(found) != set(REQUIRED):
        raise ValueError('Missing required linked allocations')
    rows = sorted(found.values(), key=lambda x: x['start'])
    if any(a['end_exclusive'] > b['start'] for a, b in zip(rows, rows[1:])):
        raise ValueError('Overlapping linked allocations')
    return found


def audit(elf, nm='nm'):
    raw = subprocess.run([nm, '-S', '-n', str(elf)], check=True, capture_output=True,
                         text=True, timeout=20).stdout
    return dict(status='OFFLINE_LINKED_GEM_MEMORY_NOT_OWNERSHIP', hardware_executed=False,
                elf=dict(path=str(elf.resolve()), sha256=hashlib.sha256(elf.read_bytes()).hexdigest()),
                linked_allocations=symbols(raw), destructive_test_allowed=False,
                limits='Static ELF allocations only, not live queue pointers or pbuf chains. TX can reference other pools or application payloads; excluding these five ranges alone cannot authorize a DDR write test.'), raw


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--elf', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    if a.output.exists():
        p.error('Use fresh output directory')
    result, raw = audit(a.elf)
    a.output.mkdir(parents=True)
    (a.output / 'symbols.log').write_text(raw)
    (a.output / 'results.json').write_text(json.dumps(result, indent=2) + '\n')
