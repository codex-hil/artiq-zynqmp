#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Offline policy checks under ASan/UBSan plus independent unsafe mutants."""
import argparse,hashlib,json,shutil,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
src=Path(__file__).resolve().parent;header=src/'master_network_admission.h';original=header.read_text();results={}
(a.output/'results.json').write_text('{"status":"INCOMPLETE"}\n')
mutants={'baseline':None,'ignore-generation':('||generation!=p->generation',''),'ignore-receipts':('||receipts!=MNE_RECEIPTS',''),'no-gate-revocation':('mfo_fault(p->gate,MNE_UNSAFE)','MNE_UNSAFE')}
for name,change in mutants.items():
 d=a.output/name;d.mkdir()
 for f in src.glob('*.h'):shutil.copy2(f,d/f.name)
 shutil.copy2(src/'test_master_network_admission.c',d/'test.c')
 if change:
  before,after=change;assert original.count(before)==1;(d/header.name).write_text(original.replace(before,after))
 cmd=['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-Wno-unused-parameter','-fno-omit-frame-pointer']
 if name=='baseline':cmd+=['-fsanitize=address,undefined']
 cmd+=[str(d/'test.c'),'-o',str(d/'test')];subprocess.run(cmd,check=True,capture_output=True,text=True,timeout=30)
 r=subprocess.run([str(d/'test')],capture_output=True,text=True,timeout=10);(d/'run.log').write_text(r.stdout+r.stderr)
 if name=='baseline':assert r.returncode==0 and 'cases=57 io_or_codec_calls=0' in r.stdout and not r.stderr
 else:assert r.returncode!=0 and 'Assertion' in r.stderr and 'NETWORK_ADMISSION_POLICY_PASS' not in r.stdout
 results[name]={'exit_code':r.returncode,'header_sha256':hashlib.sha256((d/header.name).read_bytes()).hexdigest(),'log_sha256':hashlib.sha256((d/'run.log').read_bytes()).hexdigest()}
assert header.read_text()==original
report={'status':'NETWORK_ADMISSION_57_CASES_ASAN_UBSAN_AND_THREE_MUTANT_REFUSALS_PASS','hardware_accessed':False,'source_sha256':{str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in (header,src/'test_master_network_admission.c')},'runs':results}
(a.output/'results.json').write_text(json.dumps(report,indent=2)+'\n');print(report['status'])
