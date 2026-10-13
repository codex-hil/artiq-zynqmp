"""Bounded KASLI03 bootloader-only SRAM test and diagnostic restoration.

LGPL-3.0-or-later. No runtime upload, flash operations or Genesys access.
"""
import argparse
import csv
import fcntl
import hashlib
import json
from pathlib import Path
import re
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
    args = parser.parse_args()
    qualification = json.loads(args.qualification.read_text())
    if (qualification.get('status'), qualification.get('boot_mode'),
            qualification.get('bit_sha256')) != ('BUILD_PASS_HARDWARE_NOT_RUN',
                                                  'network-only', args.sha256):
        raise SystemExit('Reviewed netboot-only build qualification required')
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
                          'bit_sha256': args.sha256, 'uart': UART,
                          'scope': 'bootloader only, restore diagnostic'}))
        return
    import serial
    from litex.tools.remote.comm_uart import CommUART
    class BoundedUART(CommUART):
        def _read(self, length):
            data = self.port.read(length)
            if len(data) != length:
                raise TimeoutError('Restored UARTBone read incomplete')
            return data

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
        for board in ('KASLI01', 'KASLI02', 'KASLI03'):
            handle = open(f'/home/codex-hil/.cache/kasli-{board}.lock', 'a')
            handles.append(handle)
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        usb = Path('/sys/bus/usb/devices/1-6.2')
        if [(usb / n).read_text().strip() for n in ('idVendor', 'idProduct', 'manufacturer')] != ['0403', '6011', 'FTDI']:
            raise RuntimeError('USB topology identity changed')
        busdev = f'{int((usb / "busnum").read_text()):03}:{int((usb / "devnum").read_text()):03}'
        result['usb_busdev'] = busdev
        base = [str(RNG / 'build/oss-cad-suite/bin/openFPGALoader'), '-c', 'ft4232',
                '--busdev-num', busdev, '--ftdi-channel', '0', '--freq', '1000000']
        identity = command(base + ['--read-dna'], 'dna.log')
        match = re.search(r'"dna":\s*"(0x[0-9a-fA-F]+)"', identity)
        if not match or int(match[1], 16) != DNA:
            raise RuntimeError('DNA mismatch')
        result['dna'] = match[1]
        with serial.Serial(UART, 115200, timeout=0.2, exclusive=True) as uart:
            uart.reset_input_buffer()
            changed = True  # Restore even if programming fails partway through.
            command(base + ['--write-sram', str(bit)], 'program.log')
            log = bytearray()
            deadline = time.monotonic() + 120
            expected = [b'Bootloader CRC passed', b'SDRAM initialized',
                        b'Memory test passed', b'Flash booting has been disabled.',
                        b'MAC=02:4b:03:48:48:54', b'IPv4=use_dhcp']
            while time.monotonic() < deadline:
                log.extend(uart.read(4096))
                if all(token in log for token in expected):
                    break
            (args.output / 'uart.log').write_bytes(log)
            if b'Booting from flash' in log or not all(token in log for token in expected):
                raise RuntimeError('Required netboot-only startup evidence absent')
            result['bootloader_test'] = 'PASS'
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
                comm = BoundedUART(UART)
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
