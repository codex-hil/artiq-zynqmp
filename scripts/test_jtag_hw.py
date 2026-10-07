#!/usr/bin/env python3
"""Host-side diagnostics; requires initialized DDR and local-rtio loaded on PL."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import time


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ['server', 'cable', 'serial', 'elf', 'psu-init', 'output']:
        p.add_argument('--' + name, required=True)
    o = p.parse_args()
    scripts = Path(__file__).resolve().parent
    output = Path(o.output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    result = {'kind': 'hardware', 'time': time.time(), 'cable': o.cable,
              'prerequisites': 'PMU/FSBL started; local-rtio configured; DDR initialized',
              'tests': {name: 'NOT_RUN' for name in ['uart', 'uart_rx', 'ddr', 'timer', 'interrupts',
              'ps_pl', 'rtio_counter', 'ttl_internal_probe', 'rtio_async_errors', 'ethernet_mdio',
              'ethernet_packets', 'ttl_physical', 'dma']}, 'logs': {}}

    def xsdb(script, *args):
        # Positional arguments survive shell parsing; no interpolation of credentials/paths.
        cmd = ['vivado-container', 'shell', '-c',
               'exec /srv/codex-hil-data/toolchains/amd/Xilinx/2025.2/Vivado/bin/xsdb "$@"',
               'xsdb', str(scripts / script), o.server, *args, o.cable]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
        (output / (script + '.log')).write_text(proc.stdout + proc.stderr)
        result['logs'][script] = proc.stdout + proc.stderr
        if proc.returncode:
            raise RuntimeError(f'{script} failed with {proc.returncode}')
        return proc.stdout

    capture = None
    try:
        with (output / 'uart.log').open('w') as log:
            capture = subprocess.Popen([sys.executable, str(scripts / 'capture_a53_uart.py'),
                       '--port', o.serial, '--output', str(output / 'uart.json'), '--timeout', '30'],
                       stdout=log, stderr=subprocess.STDOUT)
            xsdb('run_a53_ddr.tcl', o.elf)
            if capture.wait(timeout=35):
                raise RuntimeError('A53 UART/DDR diagnostic failed')
        result['tests'].update(json.loads((output / 'uart.json').read_text())['tests'])
        for script, args in [('probe_rtio_jtag.tcl', [o.psu_init]), ('probe_ethernet_jtag.tcl', [])]:
            text = xsdb(script, *args)
            for line in text.splitlines():
                fields = line.split()
                if len(fields) >= 3 and fields[0] == 'TEST' and fields[1] in result['tests']:
                    result['tests'][fields[1]] = fields[2]
        expected = ['uart', 'uart_rx', 'ddr', 'timer', 'interrupts', 'ps_pl', 'rtio_counter',
                    'ttl_internal_probe', 'rtio_async_errors', 'ethernet_mdio']
        if any(result['tests'][name] != 'PASS' for name in expected):
            raise RuntimeError('Incomplete basic diagnostic evidence')
        result['diagnostics'] = 'PASS'
    except Exception as error:
        result['failure'] = str(error)
        result['diagnostics'] = 'FAIL'
    finally:
        if capture is not None and capture.poll() is None:
            capture.terminate()
            capture.wait()
        result['complete_hardware_suite'] = 'NOT_RUN'
        (output / 'results.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result['tests'], indent=2))
    # Code 2 explicitly indicates pending physical TTL, packets and DMA.
    return 1 if result['diagnostics'] == 'FAIL' else 2


if __name__ == '__main__':
    raise SystemExit(main())
