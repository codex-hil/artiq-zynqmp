#!/usr/bin/env python3
"""Replay existing AMD PMU compile/link recipe in an isolated source copy. LGPL-3.0-or-later."""
import argparse,concurrent.futures,hashlib,json,re,shlex,subprocess
from pathlib import Path
from stage_pmu_boundary import stage

def build(source,out,lab_guard=False,vector_snapshot=False):
 if type(vector_snapshot) is not bool or (vector_snapshot and not lab_guard):raise ValueError("Vector snapshot requires explicit lab guard")
 if type(lab_guard) is not bool:raise ValueError("Explicit boolean guard selection required")
 stage(source,out);objects=out/'objects';objects.mkdir()
 entries=json.loads((source/'pmu-app/build/compile_commands.json').read_text())
 if len({Path(e['file']).name for e in entries})!=len(entries):raise ValueError('Duplicate source names')
 commands=[]
 for e in entries:
  args=shlex.split(e['command']);name=Path(e['file']).name;src=out/'src'/name
  if not src.is_file():raise ValueError('Source outside staged application')
  target=objects/(name+'.o')
  args[args.index('-o')+1]=str(target)
  args[args.index('-c')+1]=str(src)
  args+=['-I'+str(out/'src'),'-DARTIQ_PMU_BOUNDARY_TELEMETRY=1','-MF',str(target)+'.d']
  if lab_guard:args+=['-DARTIQ_PMU_LAB_GUARD=1']
  if vector_snapshot:args+=['-DARTIQ_PMU_VECTOR_SNAPSHOT=1']
  commands.append((name,args,target))
 def run(entry):
  name,args,target=entry;r=subprocess.run(args,cwd=out,text=True,capture_output=True,timeout=120)
  (objects/(name+'.log')).write_text(r.stdout+r.stderr)
  if r.returncode:raise RuntimeError('Compile failed '+name)
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(run,commands))
 ninja=(source/'pmu-app/build/build.ninja').read_text()
 block=re.search(r'^build zynqmp_pmufw.elf:.*?\n(.*?)(?=\n\n)',ninja,re.M|re.S)
 if not block:raise ValueError('Missing original link recipe')
 flags=re.search(r'^  FLAGS = (.*)$',block[1],re.M);libs=re.search(r'^  LINK_LIBRARIES = (.*)$',block[1],re.M)
 if not flags or not libs:raise ValueError('Missing link flags')
 compiler=shlex.split(entries[0]['command'])[0]
 linkargs=shlex.split(libs[1]);old_script=str(source/'pmu-app/src/lscript.ld')
 # The original path may be a preserved symlink. Replace every -T argument only.
 for i,arg in enumerate(linkargs):
  if arg.startswith('-T'):
   if Path(arg[2:]).resolve()!=(source/'pmu-app/src/lscript.ld').resolve():raise ValueError('Unexpected linker script')
   linkargs[i]='-T'+str(out/'src/lscript.ld')
 link=[compiler]+shlex.split(flags[1])+[str(t) for n,a,t in commands]+linkargs+['-Wl,-Map='+str(out/'pmufw.map'),'-o',str(out/'pmufw.elf')]
 r=subprocess.run(link,cwd=out,text=True,capture_output=True,timeout=120);(out/'link.log').write_text(r.stdout+r.stderr)
 if r.returncode:raise RuntimeError('PMU link failed; inspect link.log')
 tool=Path(compiler).parent
 for toolname,args,name in [('mb-nm',['-n','-S'],'symbols.txt'),('mb-readelf',['-lW'],'layout.txt'),('mb-size',[],'size.txt')]:
  (out/name).write_text(subprocess.check_output([str(tool/toolname)]+args+[str(out/'pmufw.elf')],text=True))
 sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 result={'status':'PMU_BOUNDARY_FIRMWARE_LINKED_NOT_HARDWARE','hardware_executed':False,'destructive_test_allowed':False,'lab_guard_enabled':lab_guard,'vector_snapshot_enabled':vector_snapshot,'elf_sha256':sha(out/'pmufw.elf'),'compile_commands':{n:a for n,a,t in commands},'link_command':link,'source_sha256':{str(p.relative_to(out)):sha(p) for p in (out/'src').iterdir() if p.is_file()},'recipe_sha256':{str(p):sha(p) for p in [source/'pmu-app/build/compile_commands.json',source/'pmu-app/build/build.ninja']},'limits':'Actual legacy recipe plus telemetry define; original BSP libraries retained. No deployment or quiescence proof.'}
 (out/'build.json').write_text(json.dumps(result,indent=2)+'\n');return result
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--lab-guard',action='store_true',help='Explicit offline build of non-returning interrupt-only lab guard, not DDR admission');p.add_argument('--vector-snapshot',action='store_true',help='Opt-in PMU-local read-only GPO0 record; requires lab guard');a=p.parse_args();r=build(a.source.resolve(),a.output.resolve(),a.lab_guard,a.vector_snapshot);print(r['status'])
