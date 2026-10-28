# SPDX-License-Identifier: LGPL-3.0-or-later
"""Bounded offline custom-unit rebuild. Never links or deploys firmware."""
import hashlib,json,shlex,struct,subprocess
from pathlib import Path
BUILD=Path('/home/codex-hil/.local/state/artiq-builds/pmu-ro-context-audit-20261028')
OUT=BUILD.parent/'pit-custom-recompile-20261028-v2'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def sections(p):
 d=p.read_bytes()
 if d[:6]!=b'\x7fELF\x01\x01':raise ValueError('expected ELF32 little endian')
 off=struct.unpack_from('<I',d,32)[0];size,count,strings=struct.unpack_from('<HHH',d,46)
 rows=[struct.unpack_from('<10I',d,off+i*size) for i in range(count)]
 s=rows[strings];names=d[s[4]:s[4]+s[5]];result={}
 for row in rows:
  n,t,flags,addr,start,length,*_=row;name=names[n:].split(b'\0',1)[0].decode()
  # Compare native allocatable code/data, not debug or compiler-private LTO IR.
  if flags&2 and t==1:result[name]={'size':length,'sha256':hashlib.sha256(d[start:start+length]).hexdigest()}
 return result

def dependencies(path):
 first=path.read_text().replace('\\\n',' ').splitlines()[0]
 return [Path(n) for n in shlex.split(first.split(':',1)[1])]
def run(cmd):
 z=subprocess.run(cmd,capture_output=True,text=True)
 if z.returncode:raise RuntimeError(z.stderr)
 return z.stdout

def main():
 OUT.mkdir(exist_ok=False)
 recipe=json.loads((BUILD/'build.json').read_text());results=[];commands=[];allpins={}
 for original in recipe['compile_commands']:
  old=Path(original[original.index('-o')+1]);new=OUT/old.name
  cmd=list(original);cmd[cmd.index('-o')+1]=str(new);cmd=[('-MD' if x=='-MMD' else x) for x in cmd]
  dep=OUT/(old.stem+'.pre.d');pre=list(cmd);pre[pre.index('-o')+1]=str(dep);pre+=['-M','-MF',str(dep)]
  run(pre);before={str(p):sha(p) for p in dependencies(dep)}
  run(cmd);after={str(p):sha(p) for p in dependencies(new.with_suffix('.d'))}
  if before!=after:raise ValueError('dependency closure or bytes changed during compile')
  allpins.update(after)
  oldsec,newsec=sections(old),sections(new)
  if not oldsec or oldsec!=newsec:raise ValueError('native code/data mismatch: '+old.name)
  objdump=str(Path(original[0]).parent/'mb-objdump')
  def reloc(p):return '\n'.join(line for line in run([objdump,'-r',*[arg for n in sorted(oldsec) for arg in ('-j',n)],str(p)]).splitlines() if 'file format' not in line)
  if reloc(old)!=reloc(new):raise ValueError('relocation mismatch: '+old.name)
  results.append({'object':old.name,'original_sha256':sha(old),'new_sha256':sha(new),'whole_object_equal':sha(old)==sha(new),'native_alloc_sections':oldsec,'native_sections_equal':True,'relocations_equal':True,'full_dependency_count':len(after),'dependencies_stable_during_compile':True})
  commands.append({'dependency_scan':pre,'compile':cmd})
 report={'hardware_executed':False,'deployable':False,'status':'TEN_CUSTOM_NATIVE_SECTIONS_AND_RELOCATIONS_MATCH','units':results,'dependency_sha256':allpins,'commands':commands,'limits':'Native fat-object comparison only. LTO IR/debug/whole-object identity not required; no new full link or vendor/BSP rebuild. Current pre/post dependency hashes are not historical attestation or independent compiler trust.'}
 (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(report,indent=2))
if __name__=='__main__':main()
