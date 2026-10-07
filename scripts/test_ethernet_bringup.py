#!/usr/bin/env python3
"""Reset the identified Genesys PS, boot AMD diagnostics, verify Ethernet."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import time
import serial


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ['server', 'cable', 'serial', 'pmu', 'fsbl', 'elf', 'output']:
        p.add_argument('--' + name, required=True)
    p.add_argument('--bitstream', type=Path, help='For integrated RTIO firmware: configure PL after PS reset/FSBL')
    p.add_argument('--psu-init', type=Path)
    p.add_argument('--interface', default='enp1s0')
    o = p.parse_args()
    scripts = Path(__file__).resolve().parent
    output = Path(o.output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    result = {'kind': 'hardware', 'time': time.time(), 'cable': o.cable,
              'scope': 'AMD bare-metal Ethernet diagnostic, not ARTIQ', 'status': 'FAIL'}
    capture = None

    def xsdb(script, *args):
        cmd = ['vivado-container', 'shell', '-c',
               'exec /srv/codex-hil-data/toolchains/amd/Xilinx/2025.2/Vivado/bin/xsdb "$@"',
               'xsdb', str(scripts / script), o.server, *args, o.cable]
        proc = subprocess.run(cmd, text=True, capture_output=True, timeout=90)
        (output / (script + '.log')).write_text(proc.stdout + proc.stderr)
        if proc.returncode:
            raise RuntimeError(f'{script} failed with {proc.returncode}')

    try:
        xsdb('reset_genesys_ps.tcl')
        with serial.Serial(o.serial, 115200, timeout=.25) as uart:
            xsdb('run_boot_firmware.tcl', o.pmu, o.fsbl)
            lines = []
            deadline = time.monotonic() + 25
            while time.monotonic() < deadline:
                line = uart.readline().decode('ascii', errors='replace').strip()
                if line:
                    lines.append(line)
                if 'Exit from FSBL' in line:
                    break
            (output / 'boot-uart.log').write_text('\n'.join(lines) + '\n')
            if not any('Exit from FSBL' in line for line in lines):
                raise RuntimeError('No completed FSBL startup on identified UART')
        if bool(o.bitstream) != bool(o.psu_init):
            raise ValueError('--bitstream and --psu-init must be supplied together')
        if o.bitstream:
            proc = subprocess.run(['vivado', '-mode', 'batch', '-source', str(scripts / 'program_genesys_pl.tcl'),
                '-log', str(output / 'program-pl.log'), '-journal', str(output / 'program-pl.jou'),
                '-tclargs', o.server.removeprefix('tcp:'), o.cable, str(o.bitstream.resolve())],
                text=True, capture_output=True, timeout=120, cwd=output)
            (output / 'program-pl.stdout').write_text(proc.stdout + proc.stderr)
            if proc.returncode: raise RuntimeError('Local RTIO bitstream configuration failed')
            xsdb('prepare_local_rtio.tcl', str(o.psu_init.resolve()))
            result['scope'] = 'AMD Ethernet and integrated Rust management transport; kernel/RPC unavailable'
        with (output / 'ethernet-uart.log').open('w') as log:
            capture = subprocess.Popen([sys.executable, str(scripts / 'capture_ethernet_uart.py'),
                       '--port', o.serial, '--output', str(output / 'uart.json')],
                       stdout=log, stderr=subprocess.STDOUT)
            xsdb('run_ethernet.tcl', o.elf)
            if capture.wait(timeout=95):
                raise RuntimeError('Ethernet firmware did not obtain DHCP lease and start echo')
        result['startup'] = json.loads((output / 'uart.json').read_text())
        ip = result['startup']['ip']
        proc = subprocess.run([sys.executable, str(scripts / 'test_ethernet_hw.py'), '--ip', ip,
                               '--interface', o.interface, '--output', str(output / 'packets.json')],
                              text=True, capture_output=True, timeout=90)
        (output / 'packets.log').write_text(proc.stdout + proc.stderr)
        result['packets'] = json.loads((output / 'packets.json').read_text())
        if proc.returncode:
            raise RuntimeError('Ethernet packet verification failed')
        xsdb('probe_ethernet_counters_jtag.tcl')
        result['mac_counters'] = (output / 'probe_ethernet_counters_jtag.tcl.log').read_text()
        result['status'] = 'PASS'
    except Exception as error:
        result['failure'] = str(error)
    finally:
        if capture is not None and capture.poll() is None:
            capture.terminate()
            capture.wait()
        (output / 'results.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
