#!/usr/bin/env python3
"""Exclusive read-only Genesys DDRC snapshot; LGPL-3.0-or-later."""
import argparse,json,os,subprocess
from pathlib import Path
from decode_ddr_config import decode
from test_candidate_runtime_hw import lease,bounded,CABLE,REPO


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--execute',action='store_true');p.add_argument('--server');p.add_argument('--output',required=True,type=Path);a=p.parse_args()
    if a.output.exists():raise ValueError('Use a fresh output directory')
    if a.execute and not a.server:p.error('--execute requires --server')
    a.output.mkdir(parents=True)
    if not a.execute:
        (a.output/'results.json').write_text(json.dumps(dict(status='READ_ONLY_DDR_CAPTURE_PLAN_NOT_EXECUTED',hardware_executed=False))+'\n');return 0
    with lease() as held:
        env=os.environ.copy();env['GENESYS_LEASE_FD']=str(held.fileno())
        command=['vivado-container','shell','-c','exec "$@"','bash','/srv/codex-hil-data/toolchains/amd/Xilinx/2025.2/Vivado/bin/xsdb',str(REPO/'scripts/probe_ddr_config.tcl'),a.server,CABLE]
        try:code,text=bounded(command,45,env,held.fileno())
        except subprocess.TimeoutExpired as error:
            text=error.output or ''
            (a.output/'snapshot.log').write_text(text.decode(errors='replace') if isinstance(text,bytes) else text)
            raise
        (a.output/'snapshot.log').write_text(text)
        if code:raise RuntimeError('DDRC snapshot failed; inspect snapshot.log')
        result=decode(text);result['hardware_executed']=True;result['cable']=CABLE
        result['scope']='Read-only configuration snapshot; no register write, CPU stop, reset or DDR memory test'
        (a.output/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2));return 0

if __name__=='__main__':raise SystemExit(main())
