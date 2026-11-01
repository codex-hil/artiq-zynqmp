# SPDX-License-Identifier: LGPL-3.0-or-later
"""Read initial BSP/ELF fields; no live register or hardware access."""
import hashlib,json,re,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
B=Path('/home/codex-hil/.local/state/artiq-builds/pit-fault-slot-minimal-audit-20261031-v1')
OUT=Path('/home/codex-hil/.local/state/artiq-builds/pit-entry-policy-20261101-v1')
BSP=Path('/srv/codex-hil-data/artiq-zynqmp/build-vivado/fsbl-spd-dump-20261022/pmu-bsp/libsrc/standalone/src')
def main():
 OUT.mkdir(exist_ok=False);sys.path.insert(0,str(ROOT/'scripts'));from package_local_candidate import loads
 d=(B/'audit-only.elf').read_bytes();sy=(B/'symbols.txt').read_text();header=BSP/'microblaze/xmicroblaze.h'
 fields=re.findall(r'\bu32\s+(\w+)\s*;',header.read_text().split('UINTPTR')[0])
 selected=['UnalignedExceptions','IopbBusException','DopbBusException','IllOpcodeException','UseStackProtection','ExceptionsInDelaySlots','UseMsrInstr','UseInterrupt','UseMmu','UseExtBrk','UseExtNmBrk']
 offsets={n:fields.index(n)*4 for n in selected};offsets['BaseVectorAddr']=308
 m=re.search(r'^([0-9a-f]+) ([0-9a-f]+) D XMicroblaze_ConfigTable$',sy,re.M);assert m
 a,z=[int(v,16) for v in m.groups()];assert z==312
 spans=[s for s in loads(d)[2] if s['address']<=a and a+z<=s['address']+s['filesz']];assert len(spans)==1;s=spans[0];raw=s['payload'][a-s['address']:a-s['address']+z]
 values={n:dict(offset=o,address=a+o,initial_value=struct.unpack_from('<I',raw,o)[0]) for n,o in offsets.items()}
 source=OUT/'offsets.c';source.write_text('#include <stddef.h>\n#include "xmicroblaze.h"\n'+''.join(f'_Static_assert(offsetof(XMicroblaze_Config,{n})=={o},"{n}");\n' for n,o in offsets.items())+'_Static_assert(sizeof(XMicroblaze_Config)==312,"size");\n')
 cmd=list(json.loads((B/'build.json').read_text())['compile_commands'][0]);cmd[cmd.index('-c')+1]=str(source);cmd[cmd.index('-o')+1]=str(OUT/'offsets.o');subprocess.run(cmd,check=True,capture_output=True)
 vectors={n:int(re.search(r'^([0-9a-f]+) [tT] '+n+'$',sy,re.M)[1],16) for n in ['_vector_reset','_vector_sw_exception','_vector_interrupt','_vector_hw_exception']}
 r=dict(status='INITIAL_BSP_ELF_ENTRY_POLICY_REVIEW_NOT_LIVE_ROUTING',hardware_executed=False,deployable=False,table_address=a,table_sha256=hashlib.sha256(raw).hexdigest(),fields=values,target_offset_static_asserts='PASS',command=cmd,elf_vectors=vectors,bsp_vector_base_matches_linked_reset=values['BaseVectorAddr']['initial_value']==vectors['_vector_reset'],live_msr_ee_eip_observed=False,hardware_configuration_verified=False,reentry_excluded=False,source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [header,BSP/'xmicroblaze_g.c']},limits='BSP software data and linked addresses only, no PVR/live vector selection/ROM shadow state or NMI/debug routing observation. Offset assertions prove compile layout, not hardware configuration.')
 (HERE/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({n:hex(v['initial_value']) for n,v in values.items()}))
if __name__=='__main__':main()
