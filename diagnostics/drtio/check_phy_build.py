#!/usr/bin/env python3
"""Validate generated PHY configuration and OOC artifact, never hardware."""
import argparse
import hashlib
import json
from pathlib import Path
import re


def check(directory, log):
    config = dict(line.split('=', 1) for line in
                  (directory / 'configuration.txt').read_text().splitlines())
    expected = {
        'CHANNEL_ENABLE': 'X0Y7', 'GT_TYPE': 'GTH',
        'TX_LINE_RATE': '2.5', 'RX_LINE_RATE': '2.5',
        'TX_USER_DATA_WIDTH': '20', 'RX_USER_DATA_WIDTH': '20',
        'TX_DATA_ENCODING': 'RAW', 'RX_DATA_DECODING': 'RAW',
        'RX_OUTCLK_SOURCE': 'RXOUTCLKPMA', 'RX_BUFFER_MODE': '1',
        'TX_BUFFER_MODE': '1', 'FREERUN_FREQUENCY': '125',
    }
    for key, value in expected.items():
        if config.get('CONFIG.' + key) != value:
            raise ValueError(f'{key}: {config.get("CONFIG." + key)!r} != {value!r}')
    reference = config['CONFIG.RX_REFCLK_FREQUENCY']
    if reference not in ('125', '156.25') or config['CONFIG.TX_REFCLK_FREQUENCY'] != reference:
        raise ValueError('Unexpected or mismatched reference clocks')
    verilog = directory / 'project/drtio_phy.gen/sources_1/ip/drtio_gth/synth/drtio_gth.v'
    source = verilog.read_text()
    for key in ('RX_OUTCLK_FREQUENCY', 'RX_USRCLK_FREQUENCY', 'TX_USRCLK_FREQUENCY'):
        match = re.search(r'C_' + key + r'=([0-9.]+)', source)
        if match is None or float(match[1]) != 125:
            raise ValueError(f'Generated {key} is not 125 MHz')
    for port in ('rxoutclk_out', 'cplllock_out', 'rxprbserr_out',
                 'loopback_in', 'gtwiz_reset_rx_cdr_stable_out'):
        if not re.search(r'(?:input|output) wire .*\b' + port + r'\b', source):
            raise ValueError(f'Missing diagnostic port: {port}')
    if 'TEST GTHE4_PHY_OOC PASS' not in log.read_text():
        raise ValueError('Vivado did not complete PHY synthesis')
    checkpoints = list(directory.rglob('*.dcp'))
    if not checkpoints:
        raise ValueError('No synthesized checkpoint')
    artifacts = [verilog, directory / 'configuration.txt', *checkpoints]
    return {'kind': 'fpga-ooc-build-not-hardware-proof', 'status': 'PASS',
            'hardware_status': 'NOT_RUN', 'refclk_mhz': float(reference),
            'rxoutclk_mhz': 125, 'line_rate_gbps': 2.5,
            'buffers': 'enabled; deterministic latency NOT_VALIDATED',
            'artifacts': [{'path': str(p), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
                          for p in artifacts]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('log', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = check(args.directory.resolve(), args.log.resolve())
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print('PASS: generated 125 MHz raw PHY and OOC checkpoint; hardware NOT_RUN')


if __name__ == '__main__':
    main()
