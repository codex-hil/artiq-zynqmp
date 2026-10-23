#!/usr/bin/env python3
"""Source-bound offline RPU observation plan; LGPL-3.0-or-later."""
import argparse
import hashlib
import json
import re
from pathlib import Path

REGISTERS = {
    'global_control': 0xff9a0000, 'r50_config': 0xff9a0100,
    'r50_status': 0xff9a0104, 'r51_config': 0xff9a0200,
    'r51_status': 0xff9a0204, 'clock_control': 0xff5e0090,
    'reset_control': 0xff5e023c,
}


def expression(text, name):
    rows = re.findall(r'^#define\s+' + re.escape(name) + r'\s+([^\n]+)$', text, re.M)
    if len(rows) != 1:
        raise ValueError('Missing/ambiguous macro ' + name)
    return re.sub(r'\s|\(u32\)|[()]', '', rows[0]).upper()


def plan(rpu, crl):
    checks = [(rpu, 'RPU_BASEADDR', '0XFF9A0000U'),
              (crl, 'CRL_APB_BASEADDR', '0XFF5E0000U')]
    for name, offset in [('RPU_RPU_GLBL_CNTL', 0), ('RPU_RPU_0_CFG', 0x100),
                         ('RPU_RPU_0_STATUS', 0x104), ('RPU_RPU_1_CFG', 0x200),
                         ('RPU_RPU_1_STATUS', 0x204)]:
        checks.append((rpu, name, f'RPU_BASEADDR+0X{offset:08X}U'))
    for name, offset in [('CRL_APB_CPU_R5_CTRL', 0x90), ('CRL_APB_RST_LPD_TOP', 0x23c)]:
        checks.append((crl, name, f'CRL_APB_BASEADDR+0X{offset:08X}U'))
    fields = [(rpu, 'RPU_RPU_GLBL_CNTL_SLSPLIT_MASK', 8),
              (crl, 'CRL_APB_CPU_R5_CTRL_CLKACT_CORE_MASK', 0x2000000),
              (crl, 'CRL_APB_CPU_R5_CTRL_CLKACT_MASK', 0x1000000),
              (crl, 'CRL_APB_RST_LPD_TOP_RPU_AMBA_RESET_MASK', 4)]
    for i in range(2):
        fields += [(rpu, f'RPU_RPU_{i}_CFG_NCPUHALT_MASK', 1),
                   (rpu, f'RPU_RPU_{i}_STATUS_NVALRESET_MASK', 32),
                   (crl, f'CRL_APB_RST_LPD_TOP_RPU_R5{i}_RESET_MASK', 1 << i)]
    checks += [(text, name, f'0X{value:08X}U') for text, name, value in fields]
    for text, name, expected in checks:
        if expression(text, name) != expected:
            raise ValueError('Changed register definition ' + name)
    return dict(status='OFFLINE_RPU_PLAN_NOT_EXECUTED', hardware_executed=False,
                registers={k: hex(v) for k, v in REGISTERS.items()}, samples=2,
                destructive_test_allowed=False, ownership='NOT_PROVEN',
                limits='Read only; no halt/reset/start/clock writes. Control bits and active-low status are separate observations, not cache or transaction-drain proof.')


def decode(samples):
    if type(samples) is not list or len(samples) != 2:
        raise ValueError('Two complete samples required')
    for sample in samples:
        if type(sample) is not dict or set(sample) != set(REGISTERS) or any(
                type(v) is not int or not 0 <= v <= 0xffffffff for v in sample.values()):
            raise ValueError('Exact unsigned 32-bit register set required')
    rows = []
    for s in samples:
        rows.append(dict(split_bit=bool(s['global_control'] & 8),
                         core_clock_enable_bit=bool(s['clock_control'] & 0x2000000),
                         peripheral_clock_enable_bit=bool(s['clock_control'] & 0x1000000),
                         amba_reset_bit=bool(s['reset_control'] & 4),
                         cores=[dict(ncpuhalt_bit=bool(s[f'r5{i}_config'] & 1),
                                     nvalreset_bit=bool(s[f'r5{i}_status'] & 32),
                                     reset_control_bit=bool(s['reset_control'] & (1 << i)))
                                for i in range(2)]))
    return dict(status='SUPPLIED_RPU_FIELDS_DECODED', hardware_executed=False,
                stable=samples[0] == samples[1], samples=rows, raw=samples,
                ownership='NOT_PROVEN', destructive_test_allowed=False)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('rpu', 'crl', 'output'):
        p.add_argument('--' + name, type=Path, required=True)
    a = p.parse_args()
    result = plan(a.rpu.read_text(), a.crl.read_text())
    result['input_sha256'] = {str(f): hashlib.sha256(f.read_bytes()).hexdigest() for f in (a.rpu, a.crl)}
    a.output.parent.mkdir(parents=True, exist_ok=True)
    with a.output.open('x') as f:
        json.dump(result, f, indent=2)
        f.write('\n')
