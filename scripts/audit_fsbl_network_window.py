#!/usr/bin/env python3
"""Offline FSBL/PMU network-window evidence; LGPL-3.0-or-later."""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

ANCHORS = {
 'app/src/xfsbl_initialization.c': ['case XFSBL_JTAG_BOOT_MODE:', 'Status = XFSBL_STATUS_JTAG;',
                                  'FsblInstancePtr->DeviceOps.DeviceInit(BootMode)'],
 'app/src/xfsbl_main.c': ['else if (XFSBL_STATUS_JTAG == FsblStatus)',
                        'Xil_Out32(XFSBL_R5_USAGE_STATUS_REG,', 'FsblStage = XFSBL_STAGE4;'],
 'app/src/psu_init.c': ['GEM 0 reset', '0x00000001U, 0x00000000U);'],
 'pmu-app/src/pm_reset.c': ['static PmResetRom pmResetGem0', '.pulseRom = &XpbrRstGem0Handler,']}


def symbol_names(text):
    return [line.split()[-1] for line in text.splitlines()
            if re.match(r'^[0-9a-fA-F]+\s+[A-Za-z]\s+\S+$', line)]


def audit(root):
    result = dict(status='OFFLINE_BOOT_WINDOW_AUDIT_NOT_ADMITTED', hardware_executed=False,
                  sources=[], images={}, destructive_test_allowed=False,
                  limits='Missing network symbols are negative evidence only. Generic MMIO, ROM callbacks, boot-mode state and live transaction drain are not proven by symbol inspection.')
    for rel, anchors in ANCHORS.items():
        p = root / rel
        lines = p.read_text().splitlines()
        hits = {a: [i for i, line in enumerate(lines, 1) if a in line] for a in anchors}
        if not all(hits.values()):
            raise ValueError('Required source anchor missing: ' + rel)
        result['sources'].append(dict(path=str(p.resolve()), sha256=hashlib.sha256(p.read_bytes()).hexdigest(), anchors=hits))
    raw = {}
    for role, rel in [('fsbl', 'app/build/zynqmp_fsbl.elf'), ('pmu', 'pmu-app/build/zynqmp_pmufw.elf')]:
        p = root / rel
        text = subprocess.run(['nm', str(p)], check=True, capture_output=True, text=True, timeout=20).stdout
        names = symbol_names(text)
        raw[role] = text
        result['images'][role] = dict(path=str(p.resolve()), sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
            named_network_symbols=[n for n in names if re.search(r'XEmacPs|lwip|xemacps|ethernet|netif', n, re.I)],
            reset_related_symbols=[n for n in names if 'Reset' in n])
    return result, raw


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    if a.output.exists():p.error('Use fresh output')
    result, raw = audit(a.build)
    a.output.mkdir(parents=True)
    for role, text in raw.items():(a.output / (role + '-symbols.log')).write_text(text)
    (a.output / 'results.json').write_text(json.dumps(result, indent=2) + '\n')
