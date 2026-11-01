# SPDX-License-Identifier: LGPL-3.0-or-later
"""Static non-PMU relocation fixture only, never a firmware/HW launcher."""
import hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
OUT=Path('/home/codex-hil/.local/state/artiq-builds/pit-fault-entry-link-20261101-v1')
def main():
 OUT.mkdir(exist_ok=False)
 tool=Path('/srv/codex-hil-data/toolchains/amd/Xilinx/2025.2/Vivado/gnu/microblaze/lin/bin')
 obj=Path('/home/codex-hil/.local/state/artiq-builds/pit-fault-entry-object-20261101-v1/entry.o')
 sys.path.insert(0,str(ROOT/'scripts'));from check_pit_fault_entry_object import check
 check(obj.read_bytes())
 cmd=[str(tool/'mb-ld'),'-EL','--no-relax','-T',str(HERE/'audit-only.ld'),str(obj),'-o',str(OUT/'fixture.elf')]
 z=subprocess.run(cmd,capture_output=True,text=True);(HERE/'link.log').write_text(z.stdout+z.stderr)
 if z.returncode:raise RuntimeError(z.stderr)
 for name,args,out in [('mb-objdump',['-d',str(OUT/'fixture.elf')],'linked.dis'),('mb-nm',['-S',str(OUT/'fixture.elf')],'symbols.txt'),('mb-readelf',['-lSWr',str(OUT/'fixture.elf')],'elf-layout.txt')]:
  (HERE/out).write_text(subprocess.check_output([str(tool/name),*args],text=True))
 data=(OUT/'fixture.elf').read_bytes();(HERE/'fixture.hex').write_text(data.hex()+'\n')
 (HERE/'build.json').write_text(json.dumps(dict(status='SYNTHETIC_NON_PMU_LINK_PASS_NOT_FIRMWARE',hardware_executed=False,deployable=False,command=cmd,object_sha256=hashlib.sha256(obj.read_bytes()).hexdigest(),linker_sha256=hashlib.sha256((HERE/'audit-only.ld').read_bytes()).hexdigest(),elf_sha256=hashlib.sha256(data).hexdigest(),limits='Synthetic addresses 0x10000/0x20000, no PMU runtime/vector map, no execution or deployment.'),indent=2)+'\n')
if __name__=='__main__':main()
