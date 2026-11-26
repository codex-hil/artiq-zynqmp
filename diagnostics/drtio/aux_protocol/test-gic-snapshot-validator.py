#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Synthetic files only: never fabricate hardware/nesting admission."""
import argparse,copy,importlib.util,json,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
spec=importlib.util.spec_from_file_location('validator',Path(__file__).with_name('validate-gic-snapshot.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
image='a'*64

def fixture(typer=6):
 count=m.irq_count(typer);banks=[]
 for view in ('secure','nonsecure'):
  enable=[0]*((count+31)//32)
  for irq in (68,89):
   if irq<count:enable[irq//32]|=1<<(irq%32)
  dist={'ctlr':3,'typer':typer,'enable':enable,'group':[0]*((count+31)//32),'priority':[0xa0a0a0a0]*((count+3)//4),'target':[0x01010101]*((count+3)//4),'config':[0]*((count+15)//16)}
  banks.append({'view':view,'cpu':0,'current_el':3,'daif':0,'view_provenance':'SYNTHETIC ONLY: no bank accessed','ctlr':7,'pmr':240,'bpr':0,'abpr':0,'rpr':255,'distributor':dist,'read_addresses':sorted(m.addresses(count))})
 before={'banks':banks}
 return {'schema':'gic400-snapshot-v1','kind':'synthetic','capture_id':'SYNTHETIC_TEST','board_serial':'210383B7F02DA','image_sha256':image,'cpu':0,'canonical_lease':'/home/codex-hil/.cache/genesys-210383B7F02DA.lock','transport':'NONE: synthetic test','started_utc':'2026-11-26T00:00:00Z','ended_utc':'2026-11-26T00:00:01Z','before':before,'after':copy.deepcopy(before)}
base=fixture();results=[]
for typer in (0,6,31):
 f=fixture(typer);r=m.validate(f,image);assert r['structurally_complete'] and not r['hardware_admitted'] and not r['runtime_admitted'];results.append('geometry-'+str(typer))
 require_count=m.irq_count(typer);assert require_count in (32,224,1020)
mutations={
 'missing-bank':lambda f:f['before']['banks'].pop(),
 'duplicate-bank':lambda f:f['before']['banks'][1].update(view='secure'),
 'wrong-cpu':lambda f:f.update(cpu=1),
 'wrong-image':lambda f:f.update(image_sha256='b'*64),
 'missing-lease':lambda f:f.pop('canonical_lease'),
 'wrong-lease':lambda f:f.update(canonical_lease='/tmp/private.lock'),
 'empty-provenance':lambda f:f['before']['banks'][0].update(view_provenance=''),
 'missing-el':lambda f:f['before']['banks'][0].pop('current_el'),
 'bool-register':lambda f:f['before']['banks'][0].update(pmr=True),
 'bad-binary-point':lambda f:f['before']['banks'][0].update(bpr=8),
 'reversed-time':lambda f:f.update(ended_utc='2026-11-25T00:00:00Z'),
 'timezone-missing':lambda f:f.update(started_utc='2026-11-26T00:00:00'),
 'changed-bookend':lambda f:f['after']['banks'][0].update(pmr=128),
 'acknowledge-read':lambda f:f['before']['banks'][0]['read_addresses'].append(m.CPU+12),
 'extra-register':lambda f:f['before']['banks'][0]['read_addresses'].append(m.DIST+0x180),
 'duplicate-read':lambda f:f['before']['banks'][0]['read_addresses'].append(m.CPU),
 'typer-array-mismatch':lambda f:f['before']['banks'][0]['distributor'].update(typer=7),
 'input-admission-override':lambda f:f.update(hardware_admitted=True),
}
for field in ('enable','group','priority','target','config'):
 mutations['truncated-'+field]=lambda f,key=field:f['before']['banks'][0]['distributor'][key].pop()
for name,change in mutations.items():
 f=copy.deepcopy(base);change(f)
 try:m.validate(f,image)
 except (ValueError,TypeError,KeyError) as error:results.append(name)
 else:raise AssertionError('Unsafe synthetic input accepted: '+name)
# Cross-view geometry and reserved top slots cannot silently change coverage.
f=copy.deepcopy(base);f['before']['banks'][1]=fixture(7)['before']['banks'][1]
try:m.validate(f,image)
except ValueError:results.append('cross-view-geometry')
else:raise AssertionError('Inconsistent bank geometry accepted')
f=fixture(31);f['before']['banks'][0]['distributor']['enable'][-1]|=1<<31
try:m.validate(f,image)
except ValueError:results.append('reserved-top-irq')
else:raise AssertionError('Reserved IRQ bit accepted')
try:m.validate(base,'not-a-digest')
except ValueError:results.append('invalid-expected-image')
else:raise AssertionError('Malformed expected image accepted')
# Claiming real capture does not bypass the permanent no-admission result.
f=copy.deepcopy(base);f['kind']='capture';r=m.validate(f,image);assert r['status']=='STRUCTURALLY_COMPLETE_UNVERIFIED_CAPTURE' and not r['hardware_admitted'];results.append('unverified-capture-no-admission')
# Include an enabled source outside retained software range; never silently drop it.
f=copy.deepcopy(base)
for sample in ('before','after'):f[sample]['banks'][0]['distributor']['enable'][6]|=1<<8
r=m.validate(f,image);assert r['banks'][0]['enabled_outside_retained_195_irq_profile']==[200] and not r['hardware_admitted'];results.append('outside-profile-reported')
try:json.loads('{"cpu":0,"cpu":1}',object_pairs_hook=m.unique)
except ValueError:results.append('duplicate-json-key')
else:raise AssertionError('Duplicate key accepted')
synthetic=a.output/'synthetic-complete.json';synthetic.write_text(json.dumps(base,indent=2)+'\n')
command=['python3',str(Path(__file__).with_name('validate-gic-snapshot.py')),str(synthetic),'--expected-image-sha256',image,'--output',str(a.output/'synthetic-validation.json')]
r=subprocess.run(command,capture_output=True,text=True,check=True);assert 'STRUCTURALLY_COMPLETE_SYNTHETIC' in r.stdout
bad=a.output/'synthetic-truncated.json';f=copy.deepcopy(base);f['before']['banks'].pop();bad.write_text(json.dumps(f));command[2]=str(bad);command[-1]=str(a.output/'rejected-validation.json');r=subprocess.run(command,capture_output=True,text=True);assert r.returncode==2 and json.loads((a.output/'rejected-validation.json').read_text())['hardware_admitted'] is False
results+=['cli-complete','cli-rejected']
report={'status':'GIC_SNAPSHOT_SYNTHETIC_VALIDATOR_CONTROLS_PASS','checks':len(results),'controls':results,'hardware_accessed':False,'hardware_admitted':False,'limits':['All data synthetic; no actual lease acquisition, register read or bank provenance verification','Structural validation never grants runtime/nesting admission']}
(a.output/'results.json').write_text(json.dumps(report,indent=2)+'\n');print(report['status'],len(results))
