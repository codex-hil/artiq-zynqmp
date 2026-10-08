#!/usr/bin/env python3
"""Physical JB1→JB2 TTL pulse test using genuine artiq_run (jumper required)."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import time


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--ip', required=True)
    p.add_argument('--output', required=True, type=Path)
    p.add_argument('--runs', type=int, default=10)
    o = p.parse_args()
    if o.runs < 1:
        p.error('--runs must be positive')
    repo = Path(__file__).resolve().parent.parent
    out = o.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    db = out / 'device_db.py'
    db.write_text((repo/'examples/device_db_genesys.py').read_text().replace('192.168.2.16', o.ip))
    result = {'kind': 'hardware', 'time': time.time(), 'ip': o.ip,
              'scope': 'physical JB1 output/JB2 input; both edges, 100 us width',
              'status': 'FAIL', 'runs': []}
    try:
        for index in range(o.runs):
            proc = subprocess.run([str(Path(sys.executable).with_name('artiq_run')),
                '--device-db', str(db), '--dataset-db', str(out/'datasets.mdb'),
                str(repo/'examples/genesys_loopback.py')],
                capture_output=True, text=True, timeout=35)
            (out/f'run-{index}.log').write_text(proc.stdout+proc.stderr)
            result['runs'].append({'index': index, 'returncode': proc.returncode,
                                    'stdout': proc.stdout, 'stderr': proc.stderr})
            markers = [line.split()[1:] for line in proc.stdout.splitlines()
                       if line.startswith('TTL_LOOPBACK_PASS ')]
            if proc.returncode or len(markers) != 1 or 'TTL_LOOPBACK_FAIL' in proc.stdout:
                raise RuntimeError(f'Physical loopback failed on run {index}; inspect raw timestamps')
            start, rise, fall, latency, width = map(int, markers[0])
            if not (0 <= rise-start <= 32 and latency == rise-start
                    and width == fall-rise == 12500):
                raise RuntimeError('Incorrect edge/width PASS marker')
            result['runs'][-1].update(start=start, rise=rise, fall=fall,
                                     latency_mu=latency, width_mu=width)
        latencies = [r['latency_mu'] for r in result['runs']]
        if len(set(latencies)) != 1:
            raise RuntimeError('Loopback latency changed across runs')
        result.update(status='PASS', width_mu=12500, width_us=100,
                      latency_mu=latencies[0], ref_period_ns=8)
    except Exception as error:
        result['failure'] = str(error)
    (out/'results.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
