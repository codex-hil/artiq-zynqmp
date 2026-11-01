# SPDX-License-Identifier: LGPL-3.0-or-later
"""Read static ROM service declarations/ELF/loader scripts; never execute loaders."""
import hashlib,json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
SRC=Path('/home/codex-hil/.local/state/artiq-builds/pmu-fresh-no-vector-20261027/src')
B=Path('/home/codex-hil/.local/state/artiq-builds/pit-fault-slot-minimal-audit-20261031-v1')
def main():
 sys.path.insert(0,str(ROOT/'scripts'));from package_local_candidate import loads
 d=(B/'audit-only.elf').read_bytes();sy=(B/'symbols.txt').read_text();machine,entry,segs=loads(d)
 rows=re.findall(r'^([0-9a-f]+) ([0-9a-f]+) [bBdD] XpbrServExtTbl$',sy,re.M);assert len(rows)==1
 a,z=[int(v,16) for v in rows[0]];assert (a,z)==(0xffddf6e0,1024)
 spans=[s for s in segs if s['address']<=a and a+z<=s['address']+s['memsz']];assert len(spans)==1;s=spans[0]
 raw=bytes(s['payload'][a-s['address']:min(a-s['address']+z,s['filesz'])]);raw+=bytes(z-len(raw))
 ld=SRC/'lscript.ld';assert 'XpbrServHndlrTbl = 0xffd07bc8' in ld.read_text()
 paths=[SRC/n for n in ['xpfw_rom_interface.h','xpfw_rom_interface.c','pm_power.c','xpfw_start.S','lscript.ld']]+[ROOT/'scripts'/n for n in ['load_rtio_runtime.py','run_boot_firmware.tcl','restart_pmu_for_restore.tcl']]
 loader={}
 for p in paths:
  if p.suffix=='.tcl':loader[str(p.relative_to(ROOT))]=[dict(line=i,text=l.strip()) for i,l in enumerate(p.read_text().splitlines(),1) if re.search(r'\b(dow|con|rst|mwr)\b|GPO0|DEBUG_REMAP|ffd40010',l,re.I)]
 r=dict(status='STATIC_ROM_LOADER_INTERFACE_REVIEW_NOT_VECTOR_OBSERVATION',hardware_executed=False,deployable=False,elf_entry=entry,declared_rom_service_table=0xffd07bc8,ram_extension_table=dict(address=a,bytes=z,entries=z//4,initial_nonzero_bytes=sum(v!=0 for v in raw),initial_sha256=hashlib.sha256(raw).hexdigest()),loader_command_inventory=loader,source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},live_extension_table_observed=False,rom_dispatch_verified=False,remap_state_known=False,limits='Header declaration/initial ELF/script text only, not ROM code, actual PC after dow/con, executed startup, dynamic hooks or active vector route.')
 (HERE/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r['ram_extension_table']))
if __name__=='__main__':main()
