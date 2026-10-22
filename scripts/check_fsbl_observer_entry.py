#!/usr/bin/env python3
"""Offline FSBL terminal/observer entry checks; LGPL-3.0-or-later."""
import argparse
import hashlib
import json
import re
import struct
from pathlib import Path
from package_local_candidate import loads


def descriptor(data, symbols):
    machine, entry, segments = loads(data)
    matches = re.findall(r'^([0-9a-fA-F]+)\s+[tT]\s+XFsbl_Loop$', symbols, re.M)
    if machine != 183 or len(matches) != 1:
        raise ValueError('Expected unique AArch64 FSBL terminal symbol')
    pc = int(matches[0], 16)
    if not 0xfffc0000 <= pc < 0xfffffff8:
        raise ValueError('Terminal outside OCM')
    parts = [s for s in segments if s['flags'] & 1 and s['vaddr'] == s['address'] and
             s['address'] <= pc and pc + 8 <= s['address'] + s['filesz']]
    if len(parts) != 1:
        raise ValueError('Terminal not uniquely backed by executable ELF bytes')
    s = parts[0]; offset = pc - s['address']
    if s['payload'][offset:offset+8] != struct.pack('<II', 0xd503205f, 0x17ffffff):
        raise ValueError('Expected exact WFE/back-branch terminal, not a name alone')
    return dict(fsbl_sha256=hashlib.sha256(data).hexdigest(),
                symbols_sha256=hashlib.sha256(symbols.encode()).hexdigest(),
                terminal_pcs=[pc, pc + 4], hardware_executed=False)


def admit(desc, capture):
    if capture.get('fsbl_sha256') != desc['fsbl_sha256']:
        raise ValueError('Capture/image hash mismatch')
    samples = capture.get('samples')
    if not isinstance(samples, list) or len(samples) != 2:
        raise ValueError('Require exactly two stopped-state observations')
    for sample in samples:
        if sample.get('suspended') is not True or sample.get('cable') != '210383B7F02DA' or sample.get('core') != 'Cortex-A53 #0':
            raise ValueError('Wrong target or unconfirmed halt')
        for key in ('pc', 'currentel', 'sctlr_el3', 'daif', 'mpidr_el1'):
            if type(sample.get(key)) is not int or not 0 <= sample[key] < 1 << 64:
                raise ValueError('Missing/invalid register: ' + key)
        if sample['pc'] not in desc['terminal_pcs'] or sample['currentel'] != 12:
            raise ValueError('Not at selected FSBL EL3 exit loop')
        if sample['sctlr_el3'] & 0x1005 or sample['daif'] & 0x3c0 != 0x3c0:
            raise ValueError('MMU/cache enabled or exception masks not established')
        if sample['mpidr_el1'] & 0xff != 0:
            raise ValueError('Wrong affinity zero core')
    if samples[0] != samples[1]:
        raise ValueError('Stopped-state observations changed')
    return dict(status='SUPPLIED_ENTRY_OBSERVATIONS_CONSISTENT', hardware_executed=False,
                destructive_test_allowed=False,
                limits='Offline supplied-data validation only; no device provenance, lease, loader sequencing, other-master or DDR-test authorization.')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--elf', type=Path, required=True)
    p.add_argument('--symbols', type=Path, required=True)
    p.add_argument('--capture', type=Path)
    a = p.parse_args()
    d = descriptor(a.elf.read_bytes(), a.symbols.read_text())
    print(json.dumps(admit(d, json.loads(a.capture.read_text())) if a.capture else d, indent=2))
