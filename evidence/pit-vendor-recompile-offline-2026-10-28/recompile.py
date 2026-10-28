# SPDX-License-Identifier: LGPL-3.0-or-later
"""Fresh offline vendor-unit comparison; no firmware link or hardware access."""
import hashlib,importlib.util,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
p=ROOT/'evidence/pit-custom-recompile-offline-2026-10-28/recompile.py'
spec=importlib.util.spec_from_file_location('custom_compare',p);helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
BUILD=Path('/home/codex-hil/.local/state/artiq-builds/pmu-fresh-no-vector-20261027')
OUT=BUILD.parent/'pit-vendor-recompile-20261028-v2'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 OUT.mkdir(exist_ok=False)
 recipe=json.loads((BUILD/'build.json').read_text());results=[];commands=[];pins={}
 if recipe['lab_guard_enabled'] or recipe['vector_snapshot_enabled']:raise ValueError('unexpected vendor recipe')
 for name,original in recipe['compile_commands'].items():
  old=Path(original[original.index('-o')+1]);new=OUT/old.name;dep=OUT/(old.name+'.d')
  cmd=[('-MD' if x=='-MMD' else x) for x in original]
  cmd[cmd.index('-o')+1]=str(new);cmd[cmd.index('-MF')+1]=str(dep)
  pre=list(cmd);pre[pre.index('-o')+1]=str(OUT/(old.name+'.pre.d'));pre[pre.index('-MF')+1]=str(OUT/(old.name+'.pre.d'));pre+=['-M']
  helper.run(pre);before={str(p):sha(p) for p in helper.dependencies(Path(pre[pre.index('-MF')+1]))}
  helper.run(cmd);after={str(p):sha(p) for p in helper.dependencies(dep)}
  if before!=after:raise ValueError('dependency bytes changed: '+name)
  pins.update(after);a,b=helper.sections(old),helper.sections(new)
  objdump=str(Path(cmd[0]).parent/'mb-objdump')
  def reloc(p):
   if not a:return ''
   args=[objdump,'-r',*[v for n in sorted(a) for v in ('-j',n)],str(p)]
   return '\n'.join(line for line in helper.run(args).splitlines() if 'file format' not in line)
  if reloc(old)!=reloc(new):raise ValueError('native relocation mismatch: '+name)
  results.append({'unit':name,'original_native_sections':a,'new_native_sections':b,'native_sections_equal':a==b,'relocations_equal':True,'original_sha256':sha(old),'new_sha256':sha(new),'whole_object_equal':sha(old)==sha(new),'dependency_count':len(after),'dependencies_stable':True})
  commands.append({'scan':pre,'compile':cmd})
 report={'hardware_executed':False,'deployable':False,'status':'SIXTY_VENDOR_COMPARISONS_COMPLETED_NOT_IDENTICAL','units':results,'dependency_sha256':pins,'commands':commands,'limits':'Same local toolchain/source paths; full dependencies observed pre/post now. No library/BSP rebuild, original-time ancestry, full LTO link or hardware proof.'}
 (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
