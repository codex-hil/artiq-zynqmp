# SPDX-License-Identifier: LGPL-3.0-or-later
"""Assemble standalone unreferenced object; never links vectors or accesses HW."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
OUT=Path('/home/codex-hil/.local/state/artiq-builds/pit-fault-entry-object-20261101-v1')
def main():
 OUT.mkdir(exist_ok=False)
 tool=Path('/srv/codex-hil-data/toolchains/amd/Xilinx/2025.2/Vivado/gnu/microblaze/lin/bin')
 src=ROOT/'diagnostics/ddr/pit_collect/pit_fault_entry_audit.S'
 cmd=[str(tool/'mb-gcc'),'-c','-mlittle-endian','-mcpu=v9.2','-DARTIQ_PIT_FAULT_ENTRY_AUDIT_ONLY=1',str(src),'-o',str(OUT/'entry.o')]
 subprocess.run(cmd,check=True,capture_output=True)
 for name,args,out in [('mb-objdump',['-dr',str(OUT/'entry.o')],'entry.dis'),('mb-nm',['-S',str(OUT/'entry.o')],'symbols.txt'),('mb-readelf',['-SW',str(OUT/'entry.o')],'sections.txt'),('mb-readelf',['-rW',str(OUT/'entry.o')],'relocations.txt')]:
  text=subprocess.check_output([str(tool/name),*args],text=True);(HERE/out).write_text(text)
 report=dict(status='STANDALONE_ASSEMBLED_NOT_LINKED_OR_EXECUTED',hardware_executed=False,deployable=False,command=cmd,source_sha256=hashlib.sha256(src.read_bytes()).hexdigest(),object_sha256=hashlib.sha256((OUT/'entry.o').read_bytes()).hexdigest(),limits='Object only; no vector/entry/slot runtime qualification, reentry exclusion, notification preservation, external visibility, sleep or recovery.')
 (HERE/'build.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
