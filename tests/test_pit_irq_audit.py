# SPDX-License-Identifier: LGPL-3.0-or-later
"""Host doubles check callback contracts; target instructions are not executed."""
import subprocess,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class IrqAudit(unittest.TestCase):
 def test_contract_and_target_opt_in(self):
  source=ROOT/'diagnostics/ddr/pit_collect/pit_irq_audit.c'
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)
   (p/'mb_interface.h').write_text('extern unsigned calls, disables;\nunsigned fake_msr(void);\n#define mfmsr() fake_msr()\nvoid microblaze_disable_interrupts(void);\n')
   (p/'test.c').write_text('''#include <assert.h>
#include <stdint.h>
#include "pit_irq_audit.h"
unsigned calls,disables; uint32_t msr=0x18812;
unsigned fake_msr(void){calls++; return msr;}
void microblaze_disable_interrupts(void){disables++;msr &= ~2u;}
int main(void){
uint32_t value=0xdeadbeef; unsigned char bad[8];
assert(pit_irq_msr_audit((void*)1,&value)==-1);
assert(pit_irq_msr_audit(0,0)==-1);
assert(pit_irq_msr_audit(0,(uint32_t*)((uintptr_t)(bad+3)|1u))==-1);
assert(value==0xdeadbeef && calls==0);
assert(pit_irq_disable_audit((void*)1)==-1 && disables==0);
assert(pit_irq_msr_audit(0,&value)==0 && value==0x18812 && calls==1);
assert(pit_irq_disable_audit(0)==0 && disables==1 && msr==0x18810);
assert(pit_irq_msr_audit(0,&value)==0 && value==0x18810 && calls==2);
assert(pit_irq_disable_audit(0)==0 && disables==2 && msr==0x18810);
return 0;}
''')
   cmd=['cc','-std=gnu11','-O2','-Wall','-Wextra','-Werror','-I'+str(p),'-I'+str(source.parent),str(source),str(p/'test.c'),'-o',str(p/'test')]
   for flags in ([],['-D__MICROBLAZE__'],['-DARTIQ_PIT_IRQ_AUDIT_ONLY=1']):
    self.assertNotEqual(subprocess.run(cmd+flags,capture_output=True).returncode,0)
   subprocess.run(cmd+['-D__MICROBLAZE__','-DARTIQ_PIT_IRQ_AUDIT_ONLY=1'],check=True,capture_output=True)
   subprocess.run([str(p/'test')],check=True,capture_output=True)
