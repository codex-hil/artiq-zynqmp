#!/usr/bin/env python3
"""Capture startup and DHCP lease from the identified Genesys UART."""
import argparse
import ipaddress
import json
from pathlib import Path
import re
import time
import serial


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--port', required=True)
    p.add_argument('--output', required=True, type=Path)
    p.add_argument('--timeout', type=float, default=90)
    o = p.parse_args()
    result = {'kind': 'hardware', 'time': time.time(), 'port': o.port,
              'baud': 115200, 'uart_log': [], 'status': 'FAIL'}
    started = False
    dhcp = False
    ready = False
    with serial.Serial(o.port, 115200, timeout=.25) as uart:
        deadline = time.monotonic() + o.timeout
        while time.monotonic() < deadline:
            line = uart.readline().decode('ascii', errors='replace').strip()
            if not line:
                continue
            print(line, flush=True)
            if line.startswith('GENESYS-ZU GEM0 DIAGNOSTIC'):
                started = True
            if not started:
                continue
            result['uart_log'].append(line)
            if line == 'TEST ethernet_dhcp PASS':
                dhcp = True
            match = re.fullmatch(r'Board IP: (\d+\.\d+\.\d+\.\d+)', line)
            if match:
                result['ip'] = str(ipaddress.IPv4Address(match[1]))
            if line == 'TCP echo server started @ port 7':
                ready = True
                break
            if 'TEST ethernet_dhcp FAIL' in line:
                break
    if dhcp and ready and result.get('ip'):
        result['status'] = 'PASS'
    o.output.parent.mkdir(parents=True, exist_ok=True)
    o.output.write_text(json.dumps(result, indent=2) + '\n')
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
