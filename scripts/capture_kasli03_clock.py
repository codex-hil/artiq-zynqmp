"""Read-only KASLI03 Si5324 snapshot under shared hardware locks.

LGPL-3.0-or-later. I2C routing/register pointers change; no clock register data,
flash, FPGA image or runtime is written. Routing and bus CSR restored afterward.
"""
import argparse
import fcntl
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import time

RNG = Path('/home/codex-hil/rng-rpi')
UART = '/dev/serial/by-path/pci-0000:00:14.0-usb-0:6.2:1.2-port0'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--si-source', type=Path, required=True)
    parser.add_argument('--settled-timing', action='store_true')
    args = parser.parse_args()
    sys.path.insert(0, str(RNG / 'kasli'))
    from i2c import I2C
    if args.settled_timing:
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "diagnostics/kasli-master"))
        from settled_i2c import SettledI2C
        I2C = SettledI2C
    from litex.tools.remote.comm_uart import CommUART

    class BoundedUART(CommUART):
        def _read(self, length):
            data = self.port.read(length)
            if len(data) != length:
                raise TimeoutError('UARTBone short read')
            return data

        def write(self, *args, **kwargs):
            super().write(*args, **kwargs)
            self.port.flush()

    source = args.si_source.read_text()
    registers = sorted({int(r) for r in re.findall(r'\b(?:read|write|write_no_ack_value)\((\d+)', source)})
    result = {'status': 'FAIL', 'board': 'KASLI03', 'clock_configuration_written': False,
              'si_source_sha256': hashlib.sha256(source.encode()).hexdigest(),
              'timing': 'settled100us' if args.settled_timing else 'original',
              'registers': {}, 'retries': [], 'restoration_profile_validated': False}
    args.output.mkdir(parents=True, exist_ok=True)
    handles, comm, i2c, prior_csr, prior_mux = [], None, None, None, {}
    started = time.monotonic()
    try:
        for board in ('KASLI01', 'KASLI02', 'KASLI03'):
            fd = open(f'/home/codex-hil/.cache/kasli-{board}.lock', 'a')
            handles.append(fd)
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        usb = Path('/sys/bus/usb/devices/1-6.2')
        if [(usb / key).read_text().strip() for key in ('idVendor', 'idProduct', 'manufacturer')] != ['0403', '6011', 'FTDI']:
            raise RuntimeError('USB identity changed')
        busdev = f'{int((usb / "busnum").read_text()):03}:{int((usb / "devnum").read_text()):03}'
        loader = subprocess.run([str(RNG / 'build/oss-cad-suite/bin/openFPGALoader'),
                    '-c', 'ft4232', '--busdev-num', busdev, '--ftdi-channel', '0',
                    '--freq', '1000000', '--read-dna'], capture_output=True, text=True, timeout=15)
        (args.output / 'dna.log').write_text(loader.stdout + loader.stderr)
        match = re.search(r'"dna":\s*"(0x[0-9a-fA-F]+)"', loader.stdout)
        if loader.returncode or not match or int(match[1], 16) != 0x0048458a64b04854:
            raise RuntimeError('DNA mismatch')
        result.update(dna=match[1], usb_busdev=busdev)
        comm = BoundedUART(UART, csr_csv=str(RNG / 'kasli/artifacts/kasli-full-checker/csr.csv'))
        comm.port.timeout = 2
        comm.open()
        if comm.regs.diag_identity.read() != 0x4b110001:
            raise RuntimeError('Diagnostic image absent')
        prior_csr = comm.regs.i2c_w.read()
        i2c = I2C(comm)
        for address in (0x70, 0x71):
            i2c.start()
            try:
                if not i2c.put((address << 1) | 1):
                    raise RuntimeError('Mux read NACK')
                prior_mux[address] = i2c.get(last=True)
            finally:
                i2c.stop()
        result['prior_mux'] = {hex(a): value for a, value in prior_mux.items()}
        i2c.select_mux(0x70, 0)
        i2c.select_mux(0x71, 8)
        for register in registers:
            values = []
            for sample in range(2):
                for attempt in range(3):
                    if time.monotonic() - started > 90:
                        raise TimeoutError('Clock snapshot deadline')
                    try:
                        values.append(i2c.read(0x68, register, 1)[0])
                        break
                    except Exception as error:
                        result['retries'].append({'register': register, 'sample': sample,
                                                  'attempt': attempt, 'error': str(error)})
                        if attempt == 2:
                            raise
            result['registers'][str(register)] = values
        regs = result['registers']
        if (regs['134'][0] << 8 | regs['135'][0]) != 0x182:
            raise RuntimeError('Si5324 ID mismatch')
        if any(v & 1 for v in regs['130']):
            raise RuntimeError('Si5324 not locked')
        changed = [r for r, values in regs.items() if values[0] != values[1]]
        result.update(status='PASS' if not changed else 'PARTIAL', changed_registers=changed)
    except BlockingIOError:
        result.update(status='BUSY', error='Shared Kasli lock unavailable; no hardware access')
    except Exception as error:
        result['error'] = str(error)
    finally:
        if i2c is not None:
            try:
                for address, value in prior_mux.items():
                    i2c.select_mux(address, value)
                if prior_csr is not None:
                    comm.regs.i2c_w.write(prior_csr)
                result['routing_restoration'] = 'PASS'
            except Exception as error:
                result.update(status='FAIL', routing_restoration='FAIL', restore_error=str(error))
        if comm is not None:
            comm.close()
        result['session_seconds'] = round(time.monotonic() - started, 3)
        (args.output / 'results.json').write_text(json.dumps(result, indent=2) + '\n')
        for fd in reversed(handles):
            fd.close()
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result['status'] == 'PASS' else 2)


if __name__ == '__main__':
    main()
