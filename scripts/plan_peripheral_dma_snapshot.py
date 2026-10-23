#!/usr/bin/env python3
"""Offline GEM/SD/QSPI DMA observation plan; LGPL-3.0-or-later."""
import argparse
import hashlib
import json
from pathlib import Path
from plan_zdma_snapshot import macro

REGISTERS = {'gem0_network_control': 0xff0b0000,
             'sd1_present_state': 0xff170024, 'qspi_dma_status': 0xff0f0708}
FIELDS = {
 'xemacps_hw.h': {'XEMACPS_NWCTRL_OFFSET': 0, 'XEMACPS_NWCTRL_TXEN_MASK': 8,
                  'XEMACPS_NWCTRL_RXEN_MASK': 4},
 'xsdps_hw.h': {'XSDPS_PRES_STATE_OFFSET': 0x24,
                'XSDPS_PSR_INHIBIT_CMD_MASK': 1, 'XSDPS_PSR_INHIBIT_DAT_MASK': 2,
                'XSDPS_PSR_DAT_ACTIVE_MASK': 4, 'XSDPS_PSR_WR_ACTIVE_MASK': 0x100,
                'XSDPS_PSR_RD_ACTIVE_MASK': 0x200},
 'xqspipsu_hw.h': {'XQSPIPSU_QSPIDMA_DST_STS_OFFSET': 0x708,
                  'XQSPIPSU_QSPIDMA_DST_STS_BUSY_MASK': 1,
                  'XQSPIPSU_QSPIDMA_DST_STS_WR_OUTSTANDING_MASK': 0x1e,
                  'XQSPIPSU_QSPIDMA_DST_STS_DST_FIFO_LEVEL_MASK': 0x1fe0,
                  'XQSPIPSU_QSPIDMA_DST_STS_DONE_CNT_MASK': 0xe000},
 'xparameters.h': {'XPAR_XEMACPS_0_BASEADDR': 0xff0b0000,
                   'XPAR_XSDPS_0_BASEADDR': 0xff170000,
                   'XPAR_XQSPIPSU_0_BASEADDR': 0xff0f0000}}


def plan(headers):
    if set(headers) != set(FIELDS):
        raise ValueError('Exact four vendor headers required')
    for name, fields in FIELDS.items():
        for field, expected in fields.items():
            if macro(headers[name], field) != expected:
                raise ValueError('Changed peripheral definition ' + field)
    return dict(status='OFFLINE_PERIPHERAL_PLAN_NOT_EXECUTED', hardware_executed=False,
                registers={k: hex(v) for k, v in REGISTERS.items()}, samples=2,
                width_bits=32, destructive_test_allowed=False,
                limits='Only GEM NWCTRL, SD present-state, QSPI DMA STS. No FIFO/data/interrupt-status reads, triggers, reset or writes. GEM enable bits are not idle proof; excludes uninstantiated PS peripherals and PCAP ownership.')


def decode(samples):
    if type(samples) is not list or len(samples) != 2:
        raise ValueError('Two complete samples required')
    for s in samples:
        if type(s) is not dict or set(s) != set(REGISTERS) or any(
                type(v) is not int or not 0 <= v <= 0xffffffff for v in s.values()):
            raise ValueError('Exact unsigned 32-bit register set required')
    rows = []
    for s in samples:
        g, d, q = (s[n] for n in REGISTERS)
        rows.append(dict(gem_rx_enabled=bool(g & 4), gem_tx_enabled=bool(g & 8),
                         sd_command_inhibit=bool(d & 1), sd_data_inhibit=bool(d & 2),
                         sd_data_active=bool(d & 4), sd_write_active=bool(d & 0x100),
                         sd_read_active=bool(d & 0x200), qspi_dma_busy=bool(q & 1),
                         qspi_dma_outstanding=(q & 0x1e) >> 1,
                         qspi_dma_fifo_level=(q & 0x1fe0) >> 5,
                         qspi_dma_unacknowledged_done=(q & 0xe000) >> 13,
                         qspi_dma_unknown_bits=q & 0xffff0000))
    return dict(status='SUPPLIED_PERIPHERAL_FIELDS_DECODED', hardware_executed=False,
                stable=samples[0] == samples[1], raw=samples, samples=rows,
                ownership='NOT_PROVEN', destructive_test_allowed=False)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--headers', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    paths = {n: a.headers / n for n in FIELDS}
    result = plan({n: f.read_text() for n, f in paths.items()})
    result['input_sha256'] = {str(f): hashlib.sha256(f.read_bytes()).hexdigest() for f in paths.values()}
    a.output.parent.mkdir(parents=True, exist_ok=True)
    with a.output.open('x') as f:
        json.dump(result, f, indent=2)
        f.write('\n')
