#!/usr/bin/env python3
"""Verify an identified Genesys diagnostic's ICMP and byte-exact TCP echo."""
import argparse
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import socket
import subprocess
import time


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--ip', required=True, type=ipaddress.IPv4Address)
    p.add_argument('--interface', default='enp1s0')
    p.add_argument('--mac', default='02:38:3b:7f:02:0d')
    p.add_argument('--port', type=int, default=7)
    p.add_argument('--output', required=True, type=Path)
    o = p.parse_args()
    address = str(o.ip)
    result = {'kind': 'hardware', 'time': time.time(), 'ip': address, 'mac': o.mac,
              'scope': 'AMD lwIP/GEM diagnostic, not ARTIQ management/RPC',
              'tests': {'icmp': 'NOT_RUN', 'identity': 'NOT_RUN', 'tcp_echo': 'NOT_RUN'}}
    try:
        ping = subprocess.run(['ping', '-n', '-I', o.interface, '-c', '20', '-i', '0.1',
                               '-W', '1', address], capture_output=True, text=True, timeout=35)
        result['ping_log'] = ping.stdout + ping.stderr
        if ping.returncode or ' 0% packet loss' not in ping.stdout:
            raise RuntimeError('ICMP did not complete without packet loss')
        result['tests']['icmp'] = 'PASS'
        neighbor = subprocess.run(['ip', 'neigh', 'show', address, 'dev', o.interface],
                                  capture_output=True, text=True, check=True).stdout
        result['neighbor'] = neighbor
        if o.mac.lower() not in neighbor.lower().split():
            raise RuntimeError('IP neighbor does not match the Genesys diagnostic MAC')
        result['tests']['identity'] = 'PASS'
        sizes = [1, 2, 7, 63, 64, 65, 511, 512, 513, 1023, 1024, 1460, 1461, 2048, 4096, 8192]
        total = 0
        digest = hashlib.sha256()
        began = time.monotonic()
        for connection in range(5):
            with socket.create_connection((address, o.port), timeout=5) as sock:
                sock.settimeout(5)
                for size in sizes + [1024] * 200:
                    payload = os.urandom(size)
                    sock.sendall(payload)
                    received = bytearray()
                    while len(received) < size:
                        chunk = sock.recv(size - len(received))
                        if not chunk:
                            raise RuntimeError('TCP echo closed before full payload')
                        received.extend(chunk)
                    if received != payload:
                        raise RuntimeError(f'TCP mismatch connection={connection} size={size}')
                    digest.update(received)
                    total += size
        result['tests']['tcp_echo'] = 'PASS'
        result['tcp'] = {'connections': 5, 'exchanges': 1080, 'verified_bytes': total,
                         'sha256': digest.hexdigest(), 'elapsed_s': time.monotonic() - began}
    except Exception as error:
        result['failure'] = str(error)
    o.output.parent.mkdir(parents=True, exist_ok=True)
    o.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    return 1 if 'failure' in result else 0


if __name__ == '__main__':
    raise SystemExit(main())
