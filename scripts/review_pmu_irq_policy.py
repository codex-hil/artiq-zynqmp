#!/usr/bin/env python3
"""Compile maintained MicroBlaze mask helpers; no firmware deployment. LGPL-3.0-or-later."""
import argparse,hashlib,json,re,subprocess
from pathlib import Path
TOOL=Path('/srv/codex-hil-data/toolchains/amd/Xilinx/2025.2/Vivado/gnu/microblaze/lin/bin')
def mask(disassembly,name):
 if '<'+name+'>:' not in disassembly:raise ValueError('Missing helper')
 rows=[line for line in disassembly.splitlines() if re.match(r'\s*[0-9a-f]+:\s+[0-9a-f]{8}\s+',line)]
 if len(rows)!=5:raise ValueError('Unexpected helper length')
 if not all(needle in row for needle,row in zip(['mfs','andi','mts','rtsd','or'],rows)):raise ValueError('Unexpected mask helper flow')
 m=re.search(r'andi\s+r(\d+), r\1, (-?\d+)\s*$',rows[1])
 if not m:raise ValueError('Unexpected mask instruction')
 return (~int(m[2]))&0xffffffff

def review(build,out):
 if out.exists():raise ValueError('Fresh output required')
 out.mkdir(parents=True);records={}
 for name,expected in [('microblaze_disable_interrupts',2),('microblaze_disable_exceptions',0x100)]:
  src=build/'pmu-bsp/libsrc/standalone/src/microblaze'/(name+'.S');obj=out/(name+'.o')
  cmd=[str(TOOL/'mb-gcc'),'-c','-mlittle-endian','-mcpu=v9.2','-I'+str(build/'pmu-bsp/include'),str(src),'-o',str(obj)]
  subprocess.run(cmd,check=True,capture_output=True,timeout=30)
  dis=subprocess.check_output([str(TOOL/'mb-objdump'),'-d',str(obj)],text=True,timeout=10)
  (out/(name+'.dis')).write_text(dis)
  actual=mask(dis,name)
  if actual!=expected:raise ValueError('Mask policy changed')
  records[name]={'cleared_msr_mask':hex(actual),'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'object_sha256':hashlib.sha256(obj.read_bytes()).hexdigest(),'command':cmd}
 source=build/'pmu-bsp/libsrc/standalone/src/microblaze/xil_exception.c'
 text=source.read_text()
 if 'void Xil_ExceptionDisable(void)' not in text or 'microblaze_disable_exceptions();' not in text or 'microblaze_disable_interrupts();' not in text:raise ValueError('Changed exception API')
 r={'status':'MICROBLAZE_MASK_HELPERS_COMPILED_OFFLINE_NOT_EXECUTED','hardware_executed':False,'destructive_test_allowed':False,'helpers':records,'exception_api_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'decision':'Future laboratory guard should use maintained interrupt-only helper with MSR readback, preserving exception reporting; not a DDR ownership permit.','remaining':['Hardware exception/ROM/NMI/error paths remain unexcluded.','No scheduler processing after entering guard must be established in complete target control flow.','PMU-originated outstanding transactions and secondary-core releases remain separate obligations.'],'limits':'Actual objects for explicit command/BSP includes, not proof of original library build equivalence, linked guard or live MSR. Undefined canonical XPAR_MICROBLAZE_USE_MSR_INSTR selects fallback instructions here; do not assert msrclr was used.'}
 (out/'review.json').write_text(json.dumps(r,indent=2)+'\n');return r
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();print(json.dumps(review(a.build,a.output),indent=2))
