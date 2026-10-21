"""Bounded native netboot runtime startup. LGPL-3.0-or-later.

Caller holds connected-board leases and owns UART/TCP; no flash operations.
"""
import socket
import struct
import time


def execute(connection, uart, log, payload, host, scope, output, report, readiness_seconds=0):
    for attempt in range(2):
        if attempt:
            report['runtime_startup_stage']='clock-reboot:connect'
            if readiness_seconds:
                from netboot_readiness import wait
                def connect_only(timeout):
                    probe=socket.socket(socket.AF_INET6,socket.SOCK_STREAM)
                    try:
                        probe.settimeout(timeout)
                        probe.connect((host,4269,0,scope))
                        return probe
                    except Exception:
                        probe.close()
                        raise
                report['clock_reboot_readiness'],connection=wait(connect_only,readiness_seconds)
                if connection is None:raise TimeoutError('Post-clock-switch netboot readiness failed')
            else:
                connection = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
                connection.settimeout(5)
                connection.connect((host, 4269, 0, scope))
            connection.settimeout(5)
            report['runtime_startup_stage']='clock-reboot:download'
            connection.sendall(b'F' + struct.pack('>I', len(payload)))
            deadline = time.monotonic() + 30
            for offset in range(0, len(payload), 16384):
                if time.monotonic() > deadline:
                    raise TimeoutError('Second download deadline')
                connection.sendall(payload[offset:offset + 16384])
            connection.sendall(b'OK')
        offset = len(log)
        report['runtime_execute_attempted'] = True
        connection.sendall(b'B')
        report['runtime_boot_commands'] = attempt + 1
        deadline = time.monotonic() + 60
        restarted = False
        try:
            while time.monotonic() < deadline:
                log.extend(uart.read(4096))
                output.write_bytes(log)
                recent = log[offset:]
                if b'panic at ' in recent or b'halting.' in recent:
                    raise RuntimeError('Runtime panic/halt; inspect UART')
                if b'network addresses:' in recent and b'ARTIQ runtime starting' in recent:
                    report['runtime_startup'] = 'PASS'
                    report['runtime_executed'] = True
                    report['clock_profile_written'] = b'waiting for Si5324 lock' in log
                    return
                if b'Waiting for connections...' in recent:
                    restarted = True
                    break
            if not restarted:
                raise TimeoutError('Runtime startup evidence absent')
            report['clock_switch_reboot_observed'] = True
        finally:
            if attempt:
                connection.close()
    raise RuntimeError('Runtime returned to bootloader twice without startup')
