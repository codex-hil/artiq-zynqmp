# SPDX-License-Identifier: LGPL-3.0-or-later
"""Read-only current-file inventory, not retrospective build attestation."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
BUILD=Path('/home/codex-hil/.local/state/artiq-builds/pmu-ro-context-audit-20261028')
VENDOR=BUILD.parent/'pmu-fresh-no-vector-20261027'
FROZEN=BUILD.parent/'pit-ro-frozen-audit-20261028-v1/snapshot-a'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def collect():
 recipe=json.loads((BUILD/'build.json').read_text());vendor=json.loads((VENDOR/'build.json').read_text())
 groups={};missing=[]
 def pin(group,path):
  p=Path(path)
  if p.is_file():groups.setdefault(group,{})[str(p)]={'sha256':sha(p),'resolved':str(p.resolve())}
  else:missing.append({'group':group,'path':str(p)})
 for p in [BUILD/'build.json',BUILD/'audit-only.map',VENDOR/'build.json',VENDOR/'stage.json'] :pin('recipes',p)
 for cmd in recipe['compile_commands']:
  pin('custom_sources',cmd[cmd.index('-c')+1]);obj=Path(cmd[cmd.index('-o')+1]);pin('custom_objects',obj)
  pin('dependency_lists',obj.with_suffix('.d'))
 for cmd in vendor['compile_commands'].values():
  for arg in cmd:
   if arg.endswith(('.c','.S')) and Path(arg).is_file():pin('vendor_sources',arg)
 for arg in recipe['link_command']:
  if arg.endswith('.o'):pin('link_objects',arg)
  if arg.startswith('-T'):pin('linker_scripts',arg[2:])
 for line in (BUILD/'audit-only.map').read_text().splitlines():
  if line.startswith('LOAD ') and line[5:].endswith('.a'):pin('mapped_archives',line[5:])
 gcc=recipe['compile_commands'][0][0];pin('tools',gcc)
 tools={}
 for n in ['cc1','as','ld','collect2','lto1','lto-wrapper']:
  q=subprocess.run([gcc,'-print-prog-name='+n],check=True,capture_output=True,text=True).stdout.strip()
  tools[n]=q
  if Path(q).is_absolute():pin('tools',q)
 for arg in recipe['compile_commands'][0]:
  if arg.startswith('-specs='):pin('specs',arg.split('=',1)[1])
 # Current header trees are a superset: -MMD omitted system dependencies.
 cmd=recipe['compile_commands'][0];dirs=[]
 for i,arg in enumerate(cmd):
  if arg=='-isystem':dirs.append(cmd[i+1])
  elif arg.startswith('-I'):dirs.append(arg[2:])
 dirs.append(str(ROOT/'diagnostics/ddr/pit_collect'))
 for d in sorted(set(dirs)):
  for p in sorted(Path(d).rglob('*.h')):pin('current_header_superset',p)
 manifest=json.loads((FROZEN/'manifest.json').read_text());matches={n:sha(ROOT/n)==digest for n,digest in manifest['source_sha256'].items()}
 version=subprocess.run([gcc,'--version'],check=True,capture_output=True,text=True).stdout
 return {'hardware_executed':False,'deployable':False,'observation':'CURRENT_FILES_ONLY_NOT_BUILD_TIME_ATTESTATION','groups':groups,'counts':{k:len(v) for k,v in groups.items()},'missing':missing,'frozen_source_matches':matches,'gcc_version':version,'tool_resolution':tools,'gaps':['Original recipe has no build-time source/object/tool/header hash attestation.','MMD excludes system headers; current header inventory is a superset, not the exact preprocessor closure.','Vendor objects reused from a separate non-vector build; current source hashes do not prove their compilation ancestry.','Map LOAD archive paths identify candidate archives; current hashes do not prove build-time bytes or every selected member.','Tool launchers and resolved programs are inventoried, not full host/runtime/shared-library provenance.','No independent rebuild comparison yet; no reproducible-build claim.']}
if __name__=='__main__':print(json.dumps(collect(),indent=2,sort_keys=True))
