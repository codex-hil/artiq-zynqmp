#!/usr/bin/env python3
"""Bounded external PMU RAM code read, no CPU stop or private-register retry. LGPL-3.0-or-later."""
import argparse,hashlib,json,os,re,subprocess
from pathlib import Path
from test_candidate_runtime_hw import lease,REPO
from package_local_candidate import loads
from check_hw_storage import require_runtime_space
ADDRESS=0xffdc0050

def expected(path):
 data=path.read_bytes()
 if hashlib.sha256(data).hexdigest()!='243e77513f8a3feef578937d9451943d46a3a34fd62ea93fbc441e8b819eb31e':raise ValueError('Not qualified baseline PMU')
 machine,entry,parts=loads(data)
 if machine!=189 or entry!=ADDRESS:raise ValueError('Unexpected PMU image')
 words=[p['payload'][ADDRESS-p['address']:ADDRESS-p['address']+4] for p in parts if p['address']<=ADDRESS and ADDRESS+4<=p['address']+p['filesz']]
 if len(words)!=1:raise ValueError('Missing code word')
 return int.from_bytes(words[0],'little')
def parse(text,word):
 lines=text.splitlines()
 if lines.count('PMU_RAM_BEGIN')!=1 or lines.count('PMU_RAM_END')!=1:raise ValueError('Incomplete/duplicate frame')
 start,end=lines.index('PMU_RAM_BEGIN'),lines.index('PMU_RAM_END')
 rows=[s for s in lines if s.startswith('PMU_RAM ')]
 if lines[start+1:end]!=rows or len(rows)!=2:raise ValueError('Wrong frame extent')
 for i,row in enumerate(rows):
  m=re.fullmatch(r'PMU_RAM '+str(i)+r' 0xffdc0050 0x([0-9a-fA-F]{8})',row)
  if not m or int(m[1],16)!=word:raise ValueError('PMU code-word mismatch')
 return dict(status='EXTERNAL_PMU_RAM_CODE_READ_PASS',hardware_executed=True,address=hex(ADDRESS),word=hex(word),destructive_test_allowed=False,limits='AP0 reads immutable documented PMU RAM. No CPU debug memory read/stop; not telemetry coherence or PMU quiescence.')
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--pmu',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--server');p.add_argument('--execute',action='store_true');a=p.parse_args()
 word=expected(a.pmu)
 if a.output.exists():raise ValueError('Fresh output required')
 if a.execute and not a.server:raise ValueError('Server required')
 require_runtime_space(a.output,REPO);a.output.mkdir(parents=True)
 result=dict(status='PREFLIGHT_PASS_NOT_EXECUTED',hardware_executed=False,destructive_test_allowed=False)
 if a.execute:
  with lease():
   word=expected(a.pmu)
   command=['vivado-container','shell','-c','exec "$@"','bash','/srv/codex-hil-data/toolchains/amd/Xilinx/2025.2/Vivado/bin/xsdb',str(REPO/'scripts/probe_pmu_ram_access.tcl'),a.server,'210383B7F02DA']
   try:
    r=subprocess.run(command,text=True,capture_output=True,timeout=45);(a.output/'probe.log').write_text(r.stdout+r.stderr)
    if r.returncode:raise ValueError('PMU RAM read failed; no retry/force/alias')
    result=parse(r.stdout,word)
   except Exception as e:result=dict(status='FAIL',hardware_executed=True,error=str(e),destructive_test_allowed=False)
 (a.output/'results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
 if result['status']=='FAIL':raise SystemExit(1)
