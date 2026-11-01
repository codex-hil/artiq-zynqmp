# SPDX-License-Identifier: LGPL-3.0-or-later
"""Lexical/source and linked-vector trace; no WO read, target memory or HW."""
import hashlib,json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
SRC=Path('/home/codex-hil/.local/state/artiq-builds/pmu-fresh-no-vector-20261027/src')
BUILD=Path('/home/codex-hil/.local/state/artiq-builds/pit-fault-slot-minimal-audit-20261031-v1')
def main():
 paths=sorted(p for p in SRC.rglob('*') if p.suffix in ('.c','.S'))
 matches=[];pins={}
 for p in paths:
  pins[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
  for i,line in enumerate(p.read_text(errors='replace').splitlines(),1):
   if re.search(r'GPO0|DEBUG_REMAP|ffd40010',line,re.I):matches.append(dict(path=str(p),line=i,text=line.strip()))
 sy=(BUILD/'symbols.txt').read_text();dis=(BUILD/'disassembly.txt').read_text();vector_text={}
 for n in ['_vector_reset','_vector_sw_exception','_vector_interrupt','_vector_hw_exception','XPfw_Init']:
  m=re.search(r'^[0-9a-f]+ <'+n+r'>:\n.*?(?=\n[0-9a-f]+ <|\Z)',dis,re.M|re.S);assert m;vector_text[n]=m[0];(HERE/(n+'.dis')).write_text(m[0]+'\n')
 r=dict(status='STATIC_SOURCE_VECTOR_TRACE_NOT_REMAP_STATE_PROOF',hardware_executed=False,deployable=False,source_files_scanned=len(paths),source_sha256=pins,named_remap_source_matches=matches,vector_listing_sha256={n:hashlib.sha256(t.encode()).hexdigest() for n,t in vector_text.items()},linked_reset_address=0xffdc0000,bsp_base_vector_metadata=0xffd00000,write_only_gpo_read=False,remap_state_known=False,rom_code_inventoried=False,limits='Lexical absence is not no-write/control-flow proof; alias/generic MMIO, ROM/loader/debug/earlier boot and unscanned inputs remain outside scope.')
 (HERE/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(len(paths),len(matches))
if __name__=='__main__':main()
