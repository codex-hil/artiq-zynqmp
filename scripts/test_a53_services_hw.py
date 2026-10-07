#!/usr/bin/env python3
"""Test physical management with the pinned upstream client and actual CLI."""
import argparse
import json
import os
from pathlib import Path
import socket
import struct
import subprocess
import sys
import time


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--ip', required=True)
    p.add_argument('--artiq-source', required=True, type=Path)
    p.add_argument('--sipyco-source', required=True, type=Path)
    p.add_argument('--output', required=True, type=Path)
    p.add_argument('--kernel', action='store_true', help='Expect integrated bring-up kernel service')
    o = p.parse_args()
    expected_mode = 'kernel-bringup' if o.kernel else 'management-only'
    sys.path[:0] = [str(o.artiq_source), str(o.sipyco_source)]
    from artiq.coredevice.comm_mgmt import CommMgmt
    result = {'kind': 'hardware', 'time': time.time(), 'ip': o.ip,
              'scope': ('Rust management integrated with CPU1 kernel-bringup; full ARTIQ support pending' if o.kernel else 'management-only Rust firmware over maintained AMD Ethernet, not full ARTIQ runtime'),
              'tests': {}, 'client_revision': subprocess.check_output(['git', '-C', str(o.artiq_source), 'rev-parse', 'HEAD'], text=True).strip()}
    socket.setdefaulttimeout(5)
    clients = []
    def connect():
        c = CommMgmt(o.ip)
        c.open()
        c.socket.settimeout(5)
        clients.append(c)
        return c
    def raw_connection():
        s = socket.create_connection((o.ip, 1380), timeout=5)
        s.settimeout(5)
        return s
    try:
        c = connect()
        result['runtime_log'] = c.get_log()
        if not o.kernel and 'kernel execution/RPC unavailable' not in result['runtime_log']:
            raise RuntimeError('Unexpected runtime capabilities')
        metadata = {key: c.config_read(key).decode('ascii') for key in ['ip', 'mac', 'board', 'runtime_mode']}
        if metadata != {'ip': o.ip, 'mac': '02:38:3b:7f:02:0d', 'board': 'genesys_zu-5ev', 'runtime_mode': expected_mode}:
            raise RuntimeError('Unexpected target metadata')
        result['metadata'] = metadata
        result['tests']['upstream_commmgmt'] = 'PASS'
        before = int(c.config_read('rtio_counter'))
        started = time.monotonic()
        time.sleep(.5)
        after = int(c.config_read('rtio_counter'))
        elapsed = time.monotonic() - started
        estimate = (after - before) / elapsed
        if after <= before or abs(estimate - 125e6) / 125e6 > .05:
            raise RuntimeError(f'RTIO counter or nominal clock mismatch: {estimate}')
        result['rtio'] = {'before': before, 'after': after, 'estimated_hz': estimate,
                          'method': 'physical A53 MMIO -> Rust -> management TCP vs host monotonic, tolerance5%; not precision clock calibration'}
        result['tests']['a53_ps_pl_rtio_counter'] = 'PASS'
        c.clear_log()
        if c.get_log() != '':
            raise RuntimeError('ClearLog did not clear the actual log')
        result['tests']['clear_log'] = 'PASS'
        c.close(); clients.remove(c)
        # Exercise another session while the first one has a partial greeting.
        with raw_connection() as partial:
            partial.sendall(b'ARTIQ manage')
            concurrent = connect()
            if concurrent.config_read('board') != b'genesys_zu-5ev':
                raise RuntimeError('Concurrent session state collision')
            concurrent.close(); clients.remove(concurrent)
            partial.sendall(b'ment\n\0\x0c\x05\0\0\0board')
            expected = b'e\x07\x0e\0\0\0genesys_zu-5ev'
            actual = b''
            while len(actual) < len(expected):
                part = partial.recv(len(expected) - len(actual))
                if not part: raise RuntimeError('Fragmented request connection closed')
                actual += part
            if actual != expected: raise RuntimeError('Fragmented/coalesced wire response mismatch')
        result['tests']['fragmented_and_concurrent'] = 'PASS'
        with raw_connection() as bad:
            bad.sendall(b'ARTIQ management\n\0')
            if bad.recv(1) != b'e': raise RuntimeError('No handshake')
            bad.sendall(b'\x0c\xff\xff\xff\x7f')
            try:
                if bad.recv(1) != b'': raise RuntimeError('Oversized key accepted')
            except ConnectionResetError:
                pass
        result['tests']['oversized_key_rejected'] = 'PASS'
        c = connect()
        try:
            c.config_write('integration_test', b'should_not_be_saved')
        except OSError:
            result['tests']['unsupported_write_rejected'] = 'PASS'
        else:
            raise RuntimeError('Unsupported config write falsely reported success')
        c.close(); clients.remove(c)
        env = dict(os.environ)
        env['PYTHONPATH'] = str(o.artiq_source) + ':' + str(o.sipyco_source)
        cli = subprocess.run([sys.executable, '-m', 'artiq.frontend.artiq_coremgmt', '-D', o.ip, 'log'], env=env, capture_output=True, text=True, timeout=10)
        if cli.returncode or 'Management TCP connection accepted.' not in cli.stdout:
            raise RuntimeError('Real artiq_coremgmt log CLI failed: ' + cli.stderr)
        result['cli_log'] = cli.stdout
        result['tests']['real_artiq_coremgmt_cli'] = 'PASS'
        cli = subprocess.run([sys.executable, '-m', 'artiq.frontend.artiq_coremgmt', '-D', o.ip, 'config', 'read', '-s', 'board', '-s', 'runtime_mode', '-s', 'rtio_counter'], env=env, capture_output=True, text=True, timeout=10)
        values = cli.stdout.splitlines()
        if cli.returncode or len(values) != 3 or values[:2] != ['genesys_zu-5ev', expected_mode] or not values[2].isdigit():
            raise RuntimeError('Real CLI config read failed: ' + cli.stderr)
        result['cli_config'] = values
        result['tests']['real_cli_config_read'] = 'PASS'
        if o.kernel:
            from artiq.coredevice.comm_kernel import CommKernel
            worker = CommKernel(o.ip)
            worker.check_system_info()
            worker.close()
            result['tests']['kernel_system_info'] = 'PASS'
        else:
            try:
                with socket.create_connection((o.ip, 1381), timeout=2):
                    raise RuntimeError('Unexpected unvalidated kernel listener')
            except ConnectionRefusedError:
                result['tests']['no_fake_kernel_service'] = 'PASS'
        result['status'] = 'PASS'
    except Exception as error:
        result['failure'] = str(error)
        result['status'] = 'FAIL'
    finally:
        for client in clients:
            client.close()
        o.output.parent.mkdir(parents=True, exist_ok=True)
        o.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
