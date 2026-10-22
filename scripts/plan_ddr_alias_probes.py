#!/usr/bin/env python3
"""Plan sparse DDR alias probes offline; LGPL-3.0-or-later. No hardware I/O."""
import argparse
import json
from pathlib import Path

# Reviewed SDT windows. Logical offsets concatenate capacity, never the MMIO gap.
WINDOWS = ((0, 0x80000000), (0x800000000, 0x880000000))
LINE = 64
TOTAL = sum(hi - lo for lo, hi in WINDOWS)


def physical(offset):
    if not isinstance(offset, int) or isinstance(offset, bool) or offset < 0 or offset >= TOTAL or offset % LINE:
        raise ValueError('Expected aligned logical DDR offset within configured capacity')
    for lo, hi in WINDOWS:
        if offset < hi - lo:
            return lo + offset
        offset -= hi - lo
    raise AssertionError('unreachable')


def plan():
    # One pair per capacity address bit above the cache-line offset, plus
    # boundary sentinels. Later execution must write distinct tags to ALL
    # locations before reading any back; write/read-per-location misses aliasing.
    offsets = sorted({0, TOTAL - LINE, 0x80000000 - LINE, 0x80000000} |
                     {1 << bit for bit in range(6, 32)})
    probes = [dict(logical_offset=hex(o), physical_start=hex(physical(o)),
                   end_exclusive=hex(physical(o) + LINE), bytes=LINE,
                   tag_index=i) for i, o in enumerate(offsets)]
    return dict(status='OFFLINE_SPARSE_ALIAS_PLAN_NOT_ADMITTED',
                hardware_executed=False, destructive_test_allowed=False,
                configured_windows=[dict(start=hex(lo), end_exclusive=hex(hi)) for lo, hi in WINDOWS],
                configured_bytes=TOTAL, probes=probes,
                logical_address_bit_pairs=[dict(bit=b, anchor='0x0', peer=hex(1 << b)) for b in range(6, 32)],
                execution_requirements=[
                    'Preserve Piotr SPD-based DDR training before OCM handoff; cold OCM peripheral-only init is insufficient.',
                    'Verify OCM code, vectors, stack and data; no DDR-resident execution or allocations.',
                    'Establish EL3 and EL1 cache maintenance/control and physical mapping; EL1 SCTLR alone is insufficient.',
                    'Prove other A53/R5 cores, PL AXI masters and PS DMA/peripheral masters cannot access tested DDR.',
                    'Use distinct address-derived tags across every probe, barrier, then verify every probe; repeat complemented.',
                    'Bound every stage and always restore and validate the normal runtime under the shared Genesys lease.'],
                limits='Sparse logical-address probes only. Physical high-window translation, DRAM address wiring, complete capacity and sustained integrity remain unproven. No executable loader or memory writes provided.')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', required=True, type=Path)
    a = p.parse_args()
    report = plan()
    a.output.parent.mkdir(parents=True, exist_ok=True)
    with a.output.open('x') as f:
        json.dump(report, f, indent=2)
        f.write('\n')


if __name__ == '__main__':
    main()
