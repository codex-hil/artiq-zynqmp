#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Read-only retained BSP context/IRQ-frame inventory, not a live SP probe."""
import argparse,hashlib,json,re
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--bsp',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
config=a.bsp/'include/bspconfig.h';base=a.bsp/'libsrc/standalone/src/arm/ARMv8/64bit/gcc';boot=base/'boot.S';vectors=base/'asm_vectors.S'
c=config.read_text();b=boot.read_text();v=vectors.read_text();assert re.search(r'^#define\s+EL3\s+1\s*$',c,re.M),'Retained BSP execution config changed'
for anchor in ['mrs\tx0, currentEL','ldr\t x2,=EL3_stack','ldr\t x2,=EL1_stack']:
 assert b.count(anchor)==1,('Startup source changed',anchor)
start=v.index('.macro saveregister\n');registers=v[start:v.index('.endm',start)]
irq_start=v.index('IRQInterruptHandler:\n');irq=v[irq_start:v.index('bl\tIRQInterrupt',irq_start)]
def stack_push_bytes(text):return sum(int(n,16) for n in re.findall(r'\[sp,\s*#-0x([0-9a-fA-F]+)\]!',text))
register_bytes=stack_push_bytes(registers);status_bytes=stack_push_bytes(irq);assert register_bytes==176 and status_bytes==32,(register_bytes,status_bytes)
assert irq.count('saveregister')==1
r={'status':'RETAINED_EL3_BSP_AND_IRQ_FIXED_FRAME_SOURCE_AUDIT_PASS_NOT_LIVE_CONTEXT','runtime_admitted':False,'hardware_admitted':False,'retained_bsp':str(a.bsp),'configured_EL3':1,'startup':'CurrentEL selects InitEL3/InitEL1 source branches and corresponding linked stack top; actual live SP not observed','irq_fixed_frame_before_C_bytes':register_bytes+status_bytes,'general_register_save_bytes':register_bytes,'control_register_stack_save_bytes':status_bytes,'source_bindings':[],'limits':['Retained OctoberBSP artifact reference, not latestfirmware/image or activeEL/SP/IRQ observation','208bytes is fixedassembly lowerbound beforeCIRQ handler, not totalinterrupt frame or highwaterlimit','C IRQ/lwIP/Rust callbacks, exceptions, FPU-context mechanism and nesting require separatecallgraph/contextanalysis','Do not subtract lowerbound fromEL3 allocation and declare remainingcandidate budget safe','No hardwareaccess, firmware/default modifications or runtimeadmission'],'next':'Combine targetcompiler per-functionframe/contextlayout reports with exactproduction ELF/callgraph/placement and interruptbudget before any integration.'}
for f,anchor in [(config,'#define EL3'),(boot,'mrs\tx0, currentEL'),(vectors,'IRQInterruptHandler:')]:
 text=f.read_text();r['source_bindings'].append({'path':str(f),'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'anchor':anchor,'line':text[:text.index(anchor)].count('\n')+1})
a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,indent=2)+'\n');print(r['status'],'fixed_IRQ_bytes=',register_bytes+status_bytes)
