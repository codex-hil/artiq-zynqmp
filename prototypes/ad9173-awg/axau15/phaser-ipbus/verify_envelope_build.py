"""Fail closed on missing/failed timing, CDC, DRC or skew reports before RF tests."""
import argparse
import hashlib
import json
import re
from pathlib import Path


def verify(root):
    timing = (root/'timing.rpt').read_text()
    match = re.search(r'WNS\(ns\).*?\n\s*-+[^\n]*\n\s*([^\n]+)', timing, re.S)
    if match is None:raise ValueError('Missing timing summary')
    values = match[1].split()
    slacks = dict(wns_ns=float(values[0]), whs_ns=float(values[4]), wpws_ns=float(values[8]))
    if min(slacks.values()) < 0:raise ValueError(('Negative timing slack', slacks))
    for check in ('no_clock', 'unconstrained_internal_endpoints', 'loops'):
        if not re.search(r'checking '+check+r' \(0\)', timing):raise ValueError('Timing coverage: '+check)
    cdc = (root/'cdc.rpt').read_text()
    if re.search(r'CDC-\d+\s+Critical\s+[1-9]', cdc):raise ValueError('Unresolved critical CDC')
    counts = dict((name, int(count)) for name, count in re.findall(r'^(CDC-\d+)\s+(?:Info|Warning)\s+(\d+)', cdc, re.M))
    if set(counts) != {'CDC-3', 'CDC-6', 'CDC-9', 'CDC-15'} or counts.get('CDC-15') != 716 or counts.get('CDC-6') != 3:
        raise ValueError(('CDC topology changed; review required', counts))
    drc = (root/'drc.rpt').read_text()
    if re.search(r'\|\s*(?:Error|Critical Warning)\s*\|', drc):raise ValueError('DRC error')
    skew = (root/'bus-skew.rpt').read_text()
    margins = [float(v) for v in re.findall(r'Slack \(MET\)\s*:\s*([\d.]+)ns', skew)]
    if 'VIOLATED' in skew or len(margins) != 6:raise ValueError('Six passing bus-skew groups required')
    bit = root/'phaser_ipbus.bit'
    return {'status':'IMPLEMENTATION_PASS', **slacks, 'cdc_counts':counts,
            'cdc_review':{'CDC-15':'673 held DDS bits plus43 held envelope command bits, request/ack;6ns data and skew',
                          'CDC-6':'two Gray RX FIFO pointers plus2-bit result stable through8-cycle drain before ack'},
            'bus_skew_slack_ns':margins, 'bit_sha256':hashlib.sha256(bit.read_bytes()).hexdigest()}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__);p.add_argument('build', type=Path);a = p.parse_args()
    print(json.dumps(verify(a.build), indent=2))
