# SPDX-License-Identifier: LGPL-3.0-or-later
"""Create new local frozen copies and perform bounded offline replay controls."""
import hashlib,json,shutil,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
BASE=Path('/home/codex-hil/.local/state/artiq-builds/pit-mmio-word-frozen-20261030-v1')
PYTHON='/srv/codex-hil-data/artiq-zynqmp/venv/bin/python'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 a=BASE/'snapshot-a';b=BASE/'relocated/snapshot-b'
 BASE.mkdir(exist_ok=False);a.mkdir()
 original=ROOT/'evidence/pit-mmio-word-gate-offline-2026-10-30/manifest.json';m=json.loads(original.read_text())
 for group in ['source_sha256','script_sha256']:
  for name,digest in m[group].items():
   src=ROOT/name
   if sha(src)!=digest:raise ValueError('source/helper changed before freeze')
   dest=a/'repo'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dest)
 for item in m['artifacts'].values():
  src=Path(item['path'])
  if sha(src)!=item['sha256']:raise ValueError('artifact changed before freeze')
  dest=a/'artifacts'/src.name;dest.parent.mkdir(exist_ok=True);shutil.copyfile(src,dest);item['path']=str(dest.relative_to(a))
 (a/'manifest.json').write_text(json.dumps(m,indent=2)+'\n');shutil.copyfile(HERE/'replay.py',a/'replay.py')
 inventory={str(p.relative_to(a)):sha(p) for p in sorted(a.rglob('*')) if p.is_file()}
 (a/'inventory.json').write_text(json.dumps(inventory,indent=2)+'\n');anchor=sha(a/'inventory.json')
 shutil.copytree(a,b)
 def run(root,*extra,anchor_value=anchor):
  return subprocess.run([PYTHON,'-I','-B',str(root/'replay.py'),'--inventory-sha256',anchor_value,*extra],cwd='/tmp',capture_output=True,text=True,timeout=10)
 first,second=run(a),run(b)
 if first.returncode or second.returncode or first.stdout!=second.stdout:raise ValueError('isolated positive replay failed or differs: '+first.stderr+second.stderr)
 (HERE/'check.json').write_text(first.stdout);shutil.copyfile(a/'inventory.json',HERE/'inventory.json')
 controls=[]
 with tempfile.TemporaryDirectory(dir=BASE) as td:
  temp=Path(td)
  for name in inventory:
   case=temp/'case';shutil.copytree(a,case);p=case/name;p.write_bytes(p.read_bytes()+b'\n# tampered\n');z=run(case)
   if z.returncode==0:raise ValueError('changed file accepted: '+name)
   controls.append({'case':'changed-file','path':name,'rejected':True});shutil.rmtree(case)
  for label in ['missing','extra','nested-inventory','symlink','inventory-tamper','wrong-anchor','execute']:
   case=temp/label;shutil.copytree(a,case)
   if label=='missing':(case/'repo/diagnostics/ddr/pit_collect/pit_capture.c').unlink()
   elif label=='extra':(case/'extra').write_text('extra')
   elif label=='nested-inventory':(case/'repo/inventory.json').write_text('{}')
   elif label=='symlink':(case/'link').symlink_to('/tmp')
   elif label=='inventory-tamper':(case/'inventory.json').write_text('{}')
   z=run(case,*(['--execute'] if label=='execute' else []),anchor_value='0'*64 if label=='wrong-anchor' else anchor)
   if z.returncode==0:raise ValueError('negative accepted: '+label)
   controls.append({'case':label,'rejected':True,'reason':z.stderr.splitlines()[-1]})
 # Read-only owner modes are a housekeeping convention, never an access boundary.
 for root in [a,b]:
  for p in root.rglob('*'):p.chmod(0o555 if p.is_dir() else 0o444)
  root.chmod(0o555)
 result={'hardware_executed':False,'deployable':False,'copies':[str(a),str(b)],'files_excluding_inventory':len(inventory),'inventory_sha256':anchor,'positive_reports_identical':True,'negative_controls':controls,'limits':'Offline content consistency only, not trusted build provenance or a sandbox against an owner rewriting the loader. Local ELF remains outside public repo. No physical qualification.'}
 (HERE/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'files':len(inventory),'anchor':anchor,'negative_controls':len(controls)}))
if __name__=='__main__':main()
