#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Actual Rust/full-start test must reject removal of each health boundary."""
import argparse,hashlib,json,shutil,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--artiq-source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
src=Path(__file__).resolve().parent;header=src/'master_network_start.h';original=header.read_text();runs={}
(a.output/'results.json').write_text('{"status":"INCOMPLETE"}\n')
mutants={'no-pre-check':('p->active=1;int r=mnh_health_check(p);','p->active=1;int r=0;'),'no-post-check':('int health=mnh_health_check(p);if(health)r=health;','int health=0;if(health)r=health;'),'no-publication-check':('int r=p->error?p->error:mnh_health_check(p);','int r=p->error;')}
for name,(before,after) in mutants.items():
 d=a.output/name;copy=d/'source';copy.mkdir(parents=True)
 for f in src.iterdir():
  if f.is_file():shutil.copy2(f,copy/f.name)
 assert original.count(before)==1;(copy/header.name).write_text(original.replace(before,after))
 r=subprocess.run(['python3',str(copy/'build_vectors.py'),'--artiq-source',str(a.artiq_source.resolve()),'--output',str(d/'build')],capture_output=True,text=True,timeout=120)
 (d/'driver.log').write_text(r.stdout+r.stderr);log=(d/'build/build.log').read_text()
 assert r.returncode!=0 and ('Assertion' in log or 'assertion' in log) and 'TEST MASTER_NETWORK_START PASS' not in log,name
 runs[name]={'exit_code':r.returncode,'assertion_refused':True,'source_sha256':hashlib.sha256((copy/header.name).read_bytes()).hexdigest(),'log_sha256':hashlib.sha256((d/'build/build.log').read_bytes()).hexdigest()}
assert header.read_text()==original
report={'status':'THREE_NETWORK_START_HEALTH_BOUNDARY_MUTANTS_REFUSED','runs':runs,'hardware_accessed':False}
(a.output/'results.json').write_text(json.dumps(report,indent=2)+'\n');print(report['status'])
