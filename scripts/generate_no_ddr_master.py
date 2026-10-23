#!/usr/bin/env python3
"""Generate no-master diagnostic HDL without invoking Vivado; LGPL-3.0-or-later."""
import argparse,hashlib,json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for name in ['diagnostics/drtio','diagnostics/ddr','boards/genesys_zu-5ev/1_gateware']:sys.path.insert(0,str(ROOT/name))

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--ps-export',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 if a.output.exists():raise ValueError('Fresh output required')
 from diag_gateware import DiagnosticPlatform
 from gateware import Top
 platform=DiagnosticPlatform(a.ps_export);top=Top(platform,'ddr-diagnostic');platform.build(top,build_dir=str(a.output),run=False)
 rtl=(a.output/'top.v').read_text();checks={}
 for name in top.disabled_ddr_requests:
  lines=[line for line in rtl.splitlines() if 'assign '+name in line]
  if not any(re.search(r'assign '+re.escape(name)+r"(?:__SHIFTED)? = 1'd0;",s) for s in lines):raise ValueError(name+' lacks constant tie-off')
  if not any(re.search(r'assign '+re.escape(name)+r' = '+re.escape(name)+r'__SHIFTED;',s) for s in lines):raise ValueError('Missing PS alias '+name)
  checks[name]=lines
 def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
 result={'status':'FULL_HDL_GENERATED_NOT_SYNTHESIZED','hardware_executed':False,'requests':checks,'destructive_test_allowed':False,
 'limits':'Constant PL request outputs; not historical PS drain, netlist signoff or PMU/core ownership.',
 'sources':{n:sha(ROOT/n) for n in ['scripts/generate_no_ddr_master.py','boards/genesys_zu-5ev/1_gateware/gateware.py','diagnostics/ddr/no_ddr_master.py','diagnostics/drtio/diag_gateware.py']},
 'ps_inputs':{str(n):sha(Path(n)) for n in platform.ips},
 'files':{str(n.relative_to(a.output)):sha(n) for n in a.output.rglob('*') if n.is_file()}}
 (a.output/'generation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
