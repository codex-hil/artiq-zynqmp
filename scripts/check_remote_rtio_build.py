#!/usr/bin/env python3
"""Check preserved local-RTIO remote build outputs; LGPL-3.0-or-later."""
import argparse,hashlib,json,re
from pathlib import Path


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def check(build,manifest):
    if json.loads((build/'exit.json').read_text()).get('returncode')!=0:
        raise ValueError('Vivado exit code is not zero')
    for entry in manifest['files']:
        path=Path(entry['path'])
        if path.is_absolute() or '..' in path.parts:raise ValueError('Invalid input path')
        if sha(build/path)!=entry['build_sha256']:raise ValueError('Changed input: '+str(path))
    result=inspect_reports(build)
    result['status']='FPGA_BUILD_PASS_NOT_HARDWARE'
    return result


def inspect_reports(build):
    if json.loads((build/'exit.json').read_text()).get('returncode')!=0:
        raise ValueError('Vivado exit code is not zero')
    required=('top.bit','top_timing.rpt','top_drc.rpt','top_route_status.rpt','console.log')
    for name in required:
        if not (build/name).is_file() or not (build/name).stat().st_size:
            raise ValueError('Missing build artifact: '+name)
    log=(build/'console.log').read_text()
    if re.search(r'^(?:ERROR|CRITICAL WARNING):',log,re.M):
        raise ValueError('Vivado reported an error or critical warning')
    timing=(build/'top_timing.rpt').read_text()
    if 'All user specified timing constraints are met.' not in timing:
        raise ValueError('Timing did not close')
    table=re.search(r'WNS\(ns\)[^\n]*\n[^\n]*\n\s*([^\n]+)',timing)
    if not table:raise ValueError('Missing timing summary table')
    values=table[1].split()
    if len(values)!=12:raise ValueError('Unexpected timing table')
    margins=[float(values[i]) for i in (0,4,8)]
    if any(x<0 for x in margins) or any(float(values[i])!=0 for i in (1,2,5,6,9,10)):
        raise ValueError('Timing has failing endpoints/slack')
    checks={}
    for name in ('no_clock','unconstrained_internal_endpoints','no_input_delay','no_output_delay'):
        m=re.search(r'checking '+name+r' \((\d+)\)',timing)
        if not m:raise ValueError('Missing timing check: '+name)
        checks[name]=int(m[1])
    if checks['no_clock'] or checks['unconstrained_internal_endpoints']:
        raise ValueError('Internal timing coverage incomplete')
    drc=(build/'top_drc.rpt').read_text()
    rows=re.findall(r'^\|\s*([A-Z][A-Z0-9_-]*-\d+)\s*\|\s*([^|]+)\|',drc,re.M)
    if any(rule!='RTSTAT-10' or severity.strip()!='Warning' for rule,severity in rows):
        raise ValueError('Unexpected DRC violation')
    if re.search(r'\|\s*(?:Error|Critical Warning)\s*\|',drc):raise ValueError('DRC errors')
    count=re.search(r'Checks found:\s*(\d+)',drc)
    if 'REPORT SUMMARY' not in drc or not count or int(count[1])!=len(rows):
        raise ValueError('Missing/inconsistent DRC summary')
    route=(build/'top_route_status.rpt').read_text()
    m=re.search(r'# of nets with routing errors\.+\s*:\s*(\d+)',route)
    if not m or int(m[1]):raise ValueError('Routing errors or missing report')
    routable=re.search(r'# of routable nets\.+\s*:\s*(\d+)',route)
    routed=re.search(r'# of fully routed nets\.+\s*:\s*(\d+)',route)
    if not routable or not routed or int(routable[1])<=0 or routable[1]!=routed[1]:
        raise ValueError('Routing incomplete')
    return dict(status='IMPLEMENTATION_REPORTS_PASS_INPUTS_NOT_CHECKED',hardware_executed=False,
        slack_ns=dict(setup=margins[0],hold=margins[1],pulse_width=margins[2]),
        timing_coverage=checks,drc_warnings=[rule for rule,_ in rows],
        scope='Preserved HDL local RTIO/CoreDMA/analyzer/MonInj build; external I/O delays remain as reported, no physical test',
        sha256={name:sha(build/name) for name in required})


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build',type=Path,required=True);p.add_argument('--inputs',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists():raise ValueError('Refusing to overwrite report')
    result=check(a.build,json.loads(a.inputs.read_text()))
    result['input_manifest_sha256']=sha(a.inputs)
    with a.output.open('x') as f:f.write(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
