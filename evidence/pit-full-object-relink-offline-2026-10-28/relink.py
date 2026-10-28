# SPDX-License-Identifier: LGPL-3.0-or-later
"""Offline audit relink and load-segment comparison; no hardware interface."""
import hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
from package_local_candidate import loads
from check_pmu_boundary_image import check as layout
from check_pit_composition_flow import check as flow
BUILD=Path('/home/codex-hil/.local/state/artiq-builds/pmu-ro-context-audit-20261028')
NEW=BUILD.parent/'pit-custom-recompile-20261028-v2'
VENDOR=BUILD.parent/'pit-vendor-recompile-20261028-v2'
OUT=BUILD.parent/'pit-full-object-relink-20261028-v1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 OUT.mkdir(exist_ok=False)
 recipe=json.loads((BUILD/'build.json').read_text());cmd=[]
 for arg in recipe['link_command']:
  if arg.endswith('.o') and Path(arg).parent==BUILD:arg=str(NEW/Path(arg).name)
  elif arg.endswith('.o') and Path(arg).parent.name=='objects':arg=str(VENDOR/Path(arg).name)
  elif arg==str(BUILD/'audit-only.elf'):arg=str(OUT/'audit-only.elf')
  elif arg.startswith('-Wl,-Map='):arg='-Wl,-Map='+str(OUT/'audit-only.map')
  cmd.append(arg)
 inv=json.loads((ROOT/'evidence/pit-build-input-review-offline-2026-10-28/inventory.json').read_text())
 paths={Path(a) for a in cmd if a.endswith('.o')}
 for group in ['mapped_archives','linker_scripts','specs','tools']:
  paths.update(Path(p) for p in inv['groups'][group])
 before={str(p):sha(p) for p in sorted(paths)}
 z=subprocess.run(cmd,cwd=OUT,capture_output=True,text=True);(OUT/'link.log').write_text(z.stdout+z.stderr)
 if z.returncode:raise RuntimeError(z.stderr)
 after={str(p):sha(p) for p in sorted(paths)}
 if before!=after:raise ValueError('link input changed')
 elf=OUT/'audit-only.elf';prefix=Path(cmd[0]).parent
 def run(tool,args):return subprocess.run([str(prefix/tool),*args],check=True,capture_output=True,text=True).stdout
 symbols=run('mb-nm',['-n','-S',str(elf)]);dis=run('mb-objdump',['-d',str(elf)])
 (OUT/'symbols.txt').write_text(symbols);(OUT/'disassembly.txt').write_text(dis)
 undefined=run('mb-nm',['-u',str(elf)]);(OUT/'undefined.txt').write_text(undefined)
 if undefined.strip():raise ValueError('undefined symbols')
 old=loads((BUILD/'audit-only.elf').read_bytes());new=loads(elf.read_bytes())
 comparisons=[]
 for i,(a,b) in enumerate(zip(old[2],new[2])):
  comparisons.append({'index':i,'metadata_equal':{k:v for k,v in a.items() if k!='payload'}=={k:v for k,v in b.items() if k!='payload'},'payload_equal':a['payload']==b['payload'],'differences':[{'offset':j,'address':hex(a['address']+j),'old':u,'new':v} for j,(u,v) in enumerate(zip(a['payload'],b['payload'])) if u!=v],'old_sha256':hashlib.sha256(a['payload']).hexdigest(),'new_sha256':hashlib.sha256(b['payload']).hexdigest(),'bytes':len(b['payload'])})
 equal=old[:2]==new[:2] and len(old[2])==len(new[2]) and all(x['metadata_equal'] and x['payload_equal'] for x in comparisons)
 report={'hardware_executed':False,'deployable':False,'link_command':cmd,'input_sha256':before,'inputs_stable_during_link':True,'whole_elf_equal':sha(elf)==sha(BUILD/'audit-only.elf'),'old_elf_sha256':sha(BUILD/'audit-only.elf'),'new_elf_sha256':sha(elf),'load_segments_equal':equal,'segments':comparisons,'layout':layout(elf.read_bytes(),symbols),'flow':flow(elf.read_bytes(),symbols,dis,shape='ro-context-v2'),'undefined_symbols':False,'limits':'All seventy objects rebuilt; archives reused. Same local toolchain, not whole-build reproducibility, vendor ancestry or HW qualification.'}
 (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
