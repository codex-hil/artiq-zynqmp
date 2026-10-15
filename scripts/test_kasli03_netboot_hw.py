"""Bounded KASLI03 SRAM boot/download/optional runtime and restoration.

LGPL-3.0-or-later. No flash operations. Runtime option also leases Genesys.
"""
import argparse
import csv
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import socket
import struct
import sys
import subprocess
import time

DNA = 0x0048458a64b04854
UART = '/dev/serial/by-path/pci-0000:00:14.0-usb-0:6.2:1.2-port0'
RNG = Path('/home/codex-hil/rng-rpi')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--build', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--sha256', required=True)
    parser.add_argument('--qualification', type=Path, required=True)
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--network-interface', help='Optional bounded IPv6 TCP4269 negative/recovery test')
    parser.add_argument('--usb-topology', default='1-6.2')
    parser.add_argument('--uart', default=UART)
    parser.add_argument('--download-runtime', type=Path)
    parser.add_argument('--runtime-sha256')
    parser.add_argument('--execute-runtime', action='store_true')
    parser.add_argument('--management-client', action='store_true')
    parser.add_argument('--counter-experiment', action='store_true')
    parser.add_argument('--clock-plan', type=Path)
    parser.add_argument('--clock-baseline', type=Path)
    parser.add_argument('--clock-validation', type=Path)
    args = parser.parse_args()
    if args.execute_runtime:
        if not all((args.download_runtime, args.clock_plan, args.clock_baseline, args.clock_validation)):
            raise SystemExit('Execution requires payload and reviewed clock baseline/plan/physical validation')
        validation = json.loads(args.clock_validation.read_text())
        if not validation.get('restoration_profile_validated') or validation.get('status') != 'PASS':
            raise SystemExit('Clock restoration not physically validated')
        plan = json.loads(args.clock_plan.read_text())
        baseline_bytes = args.clock_baseline.read_bytes()
        baseline = json.loads(baseline_bytes)
        if hashlib.sha256(baseline_bytes).hexdigest() != plan['snapshot_sha256'] or int(validation['dna'], 16) != DNA or validation['si_source_sha256'] != baseline['si_source_sha256']:
            raise SystemExit('Clock baseline/validation identity mismatch')
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'diagnostics/kasli-master'))
        sys.path.insert(0, str(RNG / 'kasli'))
    if args.counter_experiment and not args.management_client:
        raise SystemExit('Counter experiment requires management-client and runtime checks')
    if args.management_client and not args.execute_runtime:
        raise SystemExit('Management test requires runtime execution')
    payload = None
    if args.download_runtime:
        if not args.network_interface or not args.runtime_sha256:
            raise SystemExit('RAM download requires network interface and reviewed runtime hash')
        payload = args.download_runtime.read_bytes()
        if not 0 < len(payload) <= 4 * 1024 * 1024 or hashlib.sha256(payload).hexdigest() != args.runtime_sha256:
            raise SystemExit('Runtime size/hash mismatch')
    qualification = json.loads(args.qualification.read_text())
    if (qualification.get('status'), qualification.get('boot_mode'),
            qualification.get('bit_sha256')) != ('BUILD_PASS_HARDWARE_NOT_RUN',
                                                  'network-only', args.sha256):
        raise SystemExit('Reviewed netboot-only build qualification required')
    if qualification.get('bram_boot', {}).get('cpu_reset_address') != 0:
        raise SystemExit('Qualification lacks embedded bootloader at reset address zero')
    gate = args.build / 'generated/genesys_drtio_master_v11/gateware'
    bit = gate / 'top.bit'
    if hashlib.sha256(bit.read_bytes()).hexdigest() != args.sha256:
        raise SystemExit('Bitstream hash mismatch')
    if 'All user specified timing constraints are met.' not in (gate / 'top_timing.rpt').read_text():
        raise SystemExit('Timing not accepted')
    config = json.loads((args.build / 'config.json').read_text())
    if (config['hw_rev'], config['drtio_role']) != ('v1.1', 'master'):
        raise SystemExit('Wrong revision/role')
    # Caller must review the netboot overlay and this hash before execution.
    if args.dry_run:
        print(json.dumps({'status': 'PREFLIGHT_PASS_NO_HARDWARE_ACCESS',
                          'bit_sha256': args.sha256, 'uart': args.uart,
                          'scope': 'runtime plus clock restoration' if args.execute_runtime else 'bootloader/download, restore diagnostic'}))
        return
    if args.network_interface:
        addresses = json.loads(subprocess.check_output(
            ['ip', '-j', '-6', 'addr', 'show', 'dev', args.network_interface], text=True))
        if not any(a.get('scope') == 'link' and 'tentative' not in a.get('flags', [])
                   for entry in addresses for a in entry.get('addr_info', [])):
            raise SystemExit('Host interface has no usable IPv6 link-local address; no hardware access')
    import serial
    from litex.tools.remote.comm_uart import CommUART
    class BoundedUART(CommUART):
        def _read(self, length):
            data = self.port.read(length)
            if len(data) != length:
                raise TimeoutError('Restored UARTBone read incomplete')
            return data

        def write(self, *values, **kwargs):
            super().write(*values, **kwargs)
            self.port.flush()

    args.output.mkdir(parents=True, exist_ok=True)
    result = {'status': 'FAIL', 'board': 'KASLI03', 'bit_sha256': args.sha256,
              'flash_written': False, 'runtime_uploaded': False,
              'genesys_accessed': False, 'clock_profile_written': False}
    handles, changed = [], False

    def command(argv, name):
        completed = subprocess.run(argv, text=True, capture_output=True, timeout=60)
        (args.output / name).write_text(completed.stdout + completed.stderr)
        if completed.returncode:
            raise RuntimeError(f'{name}: exit {completed.returncode}')
        return completed.stdout + completed.stderr

    try:
        locks = [f'/home/codex-hil/.cache/kasli-{board}.lock' for board in ('KASLI01', 'KASLI02', 'KASLI03')]
        if args.execute_runtime:
            locks.append('/home/codex-hil/.cache/genesys-210383B7F02DA.lock')
        for lock in sorted(locks):
            handle = open(lock, 'a')
            handles.append(handle)
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        usb = Path('/sys/bus/usb/devices') / args.usb_topology
        if [(usb / n).read_text().strip() for n in ('idVendor', 'idProduct', 'manufacturer')] != ['0403', '6011', 'FTDI']:
            raise RuntimeError('USB topology identity changed')
        busdev = f'{int((usb / "busnum").read_text()):03}:{int((usb / "devnum").read_text()):03}'
        result.update(usb_busdev=busdev, usb_topology=args.usb_topology, uart=args.uart)
        base = [str(RNG / 'build/oss-cad-suite/bin/openFPGALoader'), '-c', 'ft4232',
                '--busdev-num', busdev, '--ftdi-channel', '0', '--freq', '1000000']
        identity = command(base + ['--read-dna'], 'dna.log')
        match = re.search(r'"dna":\s*"(0x[0-9a-fA-F]+)"', identity)
        if not match or int(match[1], 16) != DNA:
            raise RuntimeError('DNA mismatch')
        result['dna'] = match[1]
        tty = Path(args.uart).resolve().name
        if f'{args.usb_topology}:1.2' not in (Path('/sys/class/tty') / tty / 'device').resolve().parts:
            raise RuntimeError('UART does not belong to selected USB topology/channel C')
        with serial.Serial(args.uart, 115200, timeout=0.2, exclusive=True) as uart:
            uart.reset_input_buffer()
            changed = True  # Restore even if programming fails partway through.
            command(base + ['--write-sram', str(bit)], 'program.log')
            log = bytearray()
            deadline = time.monotonic() + 120
            expected = [b'Bootloader CRC passed', b'SDRAM initialized',
                        b'Memory test passed', b'Flash booting has been disabled.',
                        b'MAC=02-4b-03-48-48-54', b'IPv4=use_dhcp',
                        b'Waiting for connections...']
            while time.monotonic() < deadline:
                log.extend(uart.read(4096))
                if all(token in log for token in expected):
                    break
            (args.output / 'uart.log').write_bytes(log)
            result['prior_flash_runtime_started'] = b'Booting from flash' in log
            result['clock_profile_written'] = b'waiting for Si5324 lock' in log
            if b'Booting from flash' in log or not all(token in log for token in expected):
                raise RuntimeError('Required netboot-only startup evidence absent')
            result['bootloader_test'] = 'PASS'
            result['dhcp_lease'] = 'NOT_IMPLEMENTED_BY_BOOTLOADER'
            result['netboot_ipv6_link_local'] = 'fe80::4b:3ff:fe48:4854'
            if args.network_interface:
                scope = socket.if_nametoindex(args.network_interface)
                actions = [(b'\xff', b'Received unknown netboot command: 0xff'),
                           (b'B', b'Received boot command, but no firmware downloaded')]
                for index, (request, evidence) in enumerate(actions):
                    with socket.socket(socket.AF_INET6, socket.SOCK_STREAM) as connection:
                        connection.settimeout(5)
                        connection.connect((result['netboot_ipv6_link_local'], 4269, 0, scope))
                        connection.sendall(request)
                        if connection.recv(1) != b'':
                            raise RuntimeError('Malformed netboot command did not close connection')
                    deadline = time.monotonic() + 3
                    while time.monotonic() < deadline and evidence not in log:
                        log.extend(uart.read(4096))
                    (args.output / 'uart.log').write_bytes(log)
                    if evidence not in log:
                        raise RuntimeError('Netboot command rejection evidence absent')
                with socket.socket(socket.AF_INET6, socket.SOCK_STREAM) as connection:
                    connection.settimeout(5)
                    connection.connect((result['netboot_ipv6_link_local'], 4269, 0, scope))
                neighbors = subprocess.check_output(
                    ['ip', '-j', '-6', 'neigh', 'show', 'dev', args.network_interface], text=True)
                (args.output / 'ipv6-neighbors.json').write_text(neighbors)
                matching = [entry for entry in json.loads(neighbors)
                            if entry.get('dst') == result['netboot_ipv6_link_local']]
                if not any(entry.get('lladdr', '').lower() == '02:4b:03:48:48:54' for entry in matching):
                    raise RuntimeError('Netboot neighbor MAC identity not confirmed')
                result['netboot_network'] = {
                    'status': 'PASS', 'interface': args.network_interface,
                    'tcp_connections': 3, 'unknown_command_rejected': True,
                    'boot_without_firmware_rejected': True, 'listener_recovery': True,
                    'neighbor_mac': '02:4b:03:48:48:54'}
            if payload is not None:
                with socket.socket(socket.AF_INET6, socket.SOCK_STREAM) as connection:
                    connection.settimeout(5)
                    connection.connect((result['netboot_ipv6_link_local'], 4269, 0, scope))
                    connection.sendall(b'F' + struct.pack('>I', len(payload)))
                    deadline = time.monotonic() + 30
                    for offset in range(0, len(payload), 16384):
                        if time.monotonic() >= deadline:
                            raise TimeoutError('Bounded firmware download deadline exceeded')
                        connection.sendall(payload[offset:offset + 16384])
                    connection.sendall(b'OK')
                    deadline = time.monotonic() + 10
                    while time.monotonic() < deadline and b'Firmware successfully downloaded' not in log:
                        log.extend(uart.read(4096))
                    (args.output / 'uart.log').write_bytes(log)
                    if b'Firmware successfully downloaded' not in log:
                        raise RuntimeError('Bootloader did not confirm completed RAM download')
                    if args.execute_runtime:
                        from runtime_startup import execute
                        execute(connection, uart, log, payload, result['netboot_ipv6_link_local'], scope,
                                args.output / 'uart.log', result)
                    if not args.execute_runtime and b'ARTIQ runtime starting' in log:
                        raise RuntimeError('Unexpected runtime execution')
                result['runtime_uploaded'] = True
                result['runtime_executed'] = bool(args.execute_runtime and result.get('runtime_startup') == 'PASS')
                result['ram_download'] = {'status': 'PASS', 'bytes': len(payload),
                    'source_sha256': args.runtime_sha256, 'boot_command_sent': args.execute_runtime,
                    'memory_readback': 'NOT_RUN'}
            if args.management_client:
                host_python = '/srv/codex-hil-data/artiq-zynqmp/venvs/artiq-host/bin/python'
                host = result['netboot_ipv6_link_local'] + '%' + args.network_interface
                client_env = dict(os.environ, PYTHONPATH='')
                logs = []
                for run in range(2):
                    # Runtime logs network configuration just before it binds services.
                    time.sleep(0.25)
                    completed = subprocess.run([host_python, '-m', 'artiq.frontend.artiq_coremgmt',
                        '-D', host, 'log'], capture_output=True, text=True, timeout=15, env=client_env)
                    (args.output / f'coremgmt-log-{run}.txt').write_text(completed.stdout + completed.stderr)
                    if completed.returncode:
                        raise RuntimeError(f'Standard coremgmt log failed: exit {completed.returncode}')
                    for token in ('ARTIQ runtime starting', 'genesys_drtio_master_v11',
                                  'management interface active', 'accepting network sessions'):
                        if token not in completed.stdout:
                            raise RuntimeError('Management log missing runtime identity/service evidence')
                    logs.append(len(completed.stdout))
                result['management_client'] = {'status': 'PASS', 'client': 'standard artiq_coremgmt log',
                                               'independent_connections': 2, 'log_characters': logs}
            if args.counter_experiment:
                device_db = {'core': {'type': 'local', 'module': 'artiq.coredevice.core',
                    'class': 'Core', 'arguments': {'host': host, 'target': 'rv32ima',
                    'ref_period': 1e-9, 'analyzer_proxy': None}}}
                db_path = args.output / 'device_db.py'
                db_path.write_text('device_db = ' + repr(device_db) + '\n')
                example = Path(__file__).resolve().parents[1] / 'examples/kasli_counter_probe.py'
                measured = []
                for run in range(2):
                    completed = subprocess.run([host_python, '-m', 'artiq.frontend.artiq_run',
                        '--device-db=' + str(db_path), '--dataset-db=' + str(args.output / 'datasets.mdb'),
                        str(example)], capture_output=True, text=True, timeout=30, env=client_env)
                    (args.output / f'counter-experiment-{run}.txt').write_text(completed.stdout + completed.stderr)
                    match = re.search(r'KASLI_COUNTER_RPC_PASS\s+(\d+)\s+(\d+)', completed.stdout)
                    if completed.returncode or not match or int(match[2]) - int(match[1]) < 1000000:
                        raise RuntimeError('Standard local counter/RPC experiment failed; inspect captured output')
                    measured.append({'before_mu': int(match[1]), 'after_mu': int(match[2])})
                result['counter_experiment'] = {'status': 'PASS', 'standard_artiq_run': True,
                    'runs': measured, 'ref_period': 1e-9, 'ttl_writes': False,
                    'source_sha256': hashlib.sha256(example.read_bytes()).hexdigest()}
            result['status'] = 'PASS'
    except BlockingIOError:
        result.update(status='BUSY', error='Another thread holds a shared Kasli lock; no hardware access')
    except Exception as error:
        result['error'] = str(error)
    finally:
        if changed:
            try:
                command(['python3', str(RNG / 'kasli/program_sram.py'), 'KASLI03',
                         '--busdev', result['usb_busdev'], '--dna', hex(DNA),
                         '--build', str(RNG / 'kasli/artifacts/kasli-full-checker')], 'restore.log')
                comm = BoundedUART(args.uart)
                comm.port.timeout = 2
                comm.open()
                try:
                    addresses = {row[1]: int(row[2], 0) for row in csv.reader(
                        (RNG / 'kasli/artifacts/kasli-full-checker/csr.csv').read_text().splitlines())
                        if row and row[0] == 'csr_register'}
                    for name, expected_value in [('diag_identity', 0x4b110001),
                                                  ('eem_enable', 0), ('gtp_control', 0),
                                                  ('diag_sfp_outputs', 7)]:
                        value = comm.read(addresses[name], length=1)[0]
                        if value != expected_value:
                            raise RuntimeError(f'Restored {name} mismatch: {value}')
                    result['restoration'] = 'PASS'
                    if args.execute_runtime and result.get('runtime_execute_attempted'):
                        from settled_i2c import SettledI2C
                        from clock_restore import exercise
                        bus = SettledI2C(comm)
                        plan = json.loads(args.clock_plan.read_text())
                        baseline_bytes = args.clock_baseline.read_bytes()
                        if hashlib.sha256(baseline_bytes).hexdigest() != plan['snapshot_sha256']:
                            raise RuntimeError('Clock baseline hash mismatch')
                        prior_mux = {}
                        prior_csr = comm.read(addresses['i2c_w'], length=1)[0]
                        # Attach CSR names for reused guarded diagnostic I2C implementation.
                        from litex.tools.remote.csr_builder import CSRBuilder
                        CSRBuilder.__init__(comm, comm=comm, csr_csv=str(RNG / 'kasli/artifacts/kasli-full-checker/csr.csv'))
                        try:
                            for address in (0x70, 0x71):
                                bus.start()
                                try:
                                    if not bus.put((address << 1) | 1): raise RuntimeError('Mux read NACK')
                                    prior_mux[address] = bus.get(last=True)
                                finally: bus.stop()
                            bus.select_mux(0x70, 0); bus.select_mux(0x71, 8)
                            result['clock_profile_written'] = True
                            result['clock_restore'] = {}
                            exercise(comm, bus, json.loads(baseline_bytes)['registers'], plan, result['clock_restore'])
                        finally:
                            for address, value in prior_mux.items(): bus.select_mux(address, value)
                            comm.write(addresses['i2c_w'], [prior_csr])
                finally:
                    comm.close()
            except Exception as error:
                result.update(status='FAIL', restoration='FAIL', restore_error=str(error))
        (args.output / 'results.json').write_text(json.dumps(result, indent=2) + '\n')
        for handle in reversed(handles):
            handle.close()
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result['status'] == 'PASS' else 2)


if __name__ == '__main__':
    main()
