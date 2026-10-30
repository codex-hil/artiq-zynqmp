# SPDX-License-Identifier: LGPL-3.0-or-later
"""Small offline PMU C/LTO audit build; no hardware/FPGA synthesis path."""
import hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
BASE=Path('/home/codex-hil/.local/state/artiq-builds')
OUT=BASE/'pit-mmio-word-init-audit-20261030-v1'
def main():
 OUT.mkdir(exist_ok=False)
 original=json.loads((BASE/'pmu-ro-context-audit-20261028/build.json').read_text())
 names=['pit_collect','pit_publish','pit_capture','pit_sleep_model','pit_terminal_audit','pit_terminal_record','pit_terminal_build','pit_status_compose','pit_ro_adapter','pit_mmio_read','pit_mmio_composition_audit']
 commands=[];before={}
 for n in names:
  source=ROOT/'diagnostics/ddr/pit_collect'/(n+'.c');before[str(source)]=hashlib.sha256(source.read_bytes()).hexdigest()
  cmd=list(original['compile_commands'][0]);cmd[cmd.index('-c')+1]=str(source);cmd[cmd.index('-o')+1]=str(OUT/(n+'.o'));cmd+=['-DARTIQ_PIT_MMIO_AUDIT_ONLY=1'];subprocess.run(cmd,check=True,capture_output=True,text=True);commands.append(cmd)
 prior=json.loads((BASE/'pit-full-object-relink-20261028-v1/report.json').read_text())['link_command'];link=[]
 for arg in prior:
  if arg.endswith('.o') and Path(arg).name.startswith('pit_'):continue
  if arg.startswith('-Wl,-u,pit_status_composition_audit'):continue
  if arg.endswith('/audit-only.elf'):arg=str(OUT/'audit-only.elf')
  if arg.startswith('-Wl,-Map='):arg='-Wl,-Map='+str(OUT/'audit-only.map')
  link.append(arg)
 link+=['-Wl,-u,pit_mmio_composition_audit',*[str(OUT/(n+'.o')) for n in names]]
 z=subprocess.run(link,cwd=OUT,capture_output=True,text=True);(OUT/'link.log').write_text(z.stdout+z.stderr)
 if z.returncode:raise RuntimeError(z.stderr)
 prefix=Path(link[0]).parent
 for tool,args,name in [('mb-nm',['-n','-S',str(OUT/'audit-only.elf')],'symbols.txt'),('mb-objdump',['-d',str(OUT/'audit-only.elf')],'disassembly.txt'),('mb-nm',['-u',str(OUT/'audit-only.elf')],'undefined.txt')]:
  z=subprocess.run([str(prefix/tool),*args],check=True,capture_output=True,text=True);(OUT/name).write_text(z.stdout)
 assert not (OUT/'undefined.txt').read_text().strip()
 assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in before.items())
 result={'hardware_executed':False,'deployable':False,'compile_commands':commands,'link_command':link,'custom_source_sha256':before,'elf_sha256':hashlib.sha256((OUT/'audit-only.elf').read_bytes()).hexdigest(),'vendor_objects':'reused pit-vendor-recompile-20261028-v2','limits':'Small custom C rebuild/LTO only; vendor/BSP archives reused; no main hook, mailbox, physical consumer or recovery qualification.'}
 (OUT/'build.json').write_text(json.dumps(result,indent=2)+'\n');print('LINK_PASS_NO_UNDEFINED')
if __name__=='__main__':main()
