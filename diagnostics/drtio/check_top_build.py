#!/usr/bin/env python3
"""Reject incomplete or timing-failing diagnostic builds; no hardware claims."""
import argparse
import hashlib
import json
from pathlib import Path
import re


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('build', type=Path)
    p.add_argument('--output', required=True, type=Path)
    a = p.parse_args()
    files = ('top.bit', 'top.v', 'top.xdc', 'csr-map.json', 'top_timing.rpt', 'top_bus_skew.rpt')
    for name in files:
        if not (a.build/name).is_file() or not (a.build/name).stat().st_size:
            raise ValueError('Missing artifact: '+name)
    timing = (a.build/'top_timing.rpt').read_text()
    if 'All user specified timing constraints are met.' not in timing:
        raise ValueError('Timing did not close')
    skew = (a.build/'top_bus_skew.rpt').read_text()
    if 'VIOLATED' in skew or len(re.findall(r'Slack \(MET\)', skew)) != 3:
        raise ValueError('Expected three passing Gray bus-skew constraints')
    mapping = json.loads((a.build/'csr-map.json').read_text())
    if mapping['magic'] != 0x44525430:
        raise ValueError('Wrong CSR map')
    result = {'kind':'fpga-build-not-hardware','status':'PASS',
        'scope':'separate raw GTH diagnostic; not a DRTIO satellite',
        'sha256':{n:hashlib.sha256((a.build/n).read_bytes()).hexdigest() for n in files}}
    a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__ == '__main__': main()
