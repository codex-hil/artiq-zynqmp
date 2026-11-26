#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Remove each recursion guard in private source copies; require test refusal."""
import argparse,hashlib,json,shutil,subprocess
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--artiq-source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
src=Path(__file__).resolve().parent;original=(src/'master_static_caller.c').read_bytes();a.output.mkdir(parents=True,exist_ok=False)
(a.output/'results.json').write_text('{"status":"INCOMPLETE","hardware_accessed":false}\n')
results={}
for name in ('poll','cancel','snapshot'):
 root=a.output/name;copy=root/'source';copy.mkdir(parents=True)
 for f in src.iterdir():
  if f.is_file():shutil.copy2(f,copy/f.name)
 target=copy/'master_static_caller.c';text=original.decode();start=text.index('int mfc_'+name+'(')
 before,body=text[:start],text[start:];needle=' if(mfc_active)return MFO_BUSY;';assert needle in body
 target.write_text(before+body.replace(needle,' /* test mutant: recursion guard removed */',1))
 run=subprocess.run(['python3',str(copy/'build_vectors.py'),'--artiq-source',str(a.artiq_source.resolve()),'--output',str(root/'build')],capture_output=True,text=True,timeout=120)
 (root/'driver.log').write_text(run.stdout+run.stderr)
 log=(root/'build/build.log').read_text()
 assert run.returncode!=0 and ('Assertion' in log or 'assertion' in log),'Mutant did not fail assertion: '+name
 assert 'TEST MASTER_STATIC_CALLER PASS' not in log,'Mutant published success'
 results[name]={'exit_code':run.returncode,'assertion_refusal':True,'no_static_caller_pass':True,'mutant_source_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'build_log_sha256':hashlib.sha256((root/'build/build.log').read_bytes()).hexdigest()}
assert (src/'master_static_caller.c').read_bytes()==original
r={'status':'THREE_STATIC_CALLER_REENTRY_GUARD_MUTANTS_REFUSED','source_sha256':hashlib.sha256(original).hexdigest(),'runs':results,'hardware_accessed':False}
(a.output/'results.json').write_text(json.dumps(r,indent=2)+'\n');print(r['status'])
