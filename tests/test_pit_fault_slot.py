# SPDX-License-Identifier: LGPL-3.0-or-later
import subprocess,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class Tests(unittest.TestCase):
 def test_direct_owned_slot_with_explicit_host_fence_double(self):
  base=ROOT/'diagnostics/ddr/pit_collect';source=base/'pit_fault_slot_audit.c'
  with tempfile.TemporaryDirectory() as td:
   p=Path(td);copy=p/'slot.c'
   copy.write_text('extern void test_fence(void);\n'+source.read_text().replace('__asm__ volatile("mbar 1" ::: "memory");','test_fence();'))
   (p/'main.c').write_text('''#include <assert.h>
#include <stdlib.h>
#include "pit_fault_slot_audit.h"
static unsigned fences;
void test_fence(void){assert(!pit_fault_slot_audit[0]);if(fences==0){for(unsigned i=1;i<16;i++)assert(!pit_fault_slot_audit[i]);}else{assert(pit_fault_slot_audit[1]==0x50465831&&pit_fault_slot_audit[5]==0x100);}fences++;}
int main(int argc,char **argv){assert(argc==2);int mode=atoi(argv[1]);uint32_t r[4]={0x100,0,0,0};
if(mode==1){assert(pit_fault_store_audit(3,1,r)==-1);assert(!fences);assert(pit_fault_store_audit(2,1,r)==-1);for(unsigned i=0;i<16;i++)assert(!pit_fault_slot_audit[i]);return 0;}
if(mode==2){pit_fault_slot_audit[15]=1;assert(pit_fault_store_audit(2,1,r)==-1);assert(!fences);pit_fault_slot_audit[15]=0;}
assert(pit_fault_store_audit(2,1,r)==0);assert(fences==2);assert(pit_fault_slot_audit[0]==1&&pit_fault_slot_audit[1]==0x50465831&&pit_fault_slot_audit[3]==2&&pit_fault_slot_audit[4]==1);for(unsigned i=9;i<16;i++)assert(!pit_fault_slot_audit[i]);assert(pit_fault_store_audit(2,1,r)==-1&&fences==2);return 0;}
''')
   for flags in [['-O2'],['-O1','-g','-fsanitize=address,undefined','-fno-omit-frame-pointer']]:
    exe=p/'test';subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror',*flags,'-D__MICROBLAZE__','-DARTIQ_PIT_FAULT_SLOT_AUDIT_ONLY','-I'+str(base),str(copy),str(base/'pit_fault_record.c'),str(p/'main.c'),'-o',str(exe)],check=True,capture_output=True)
    for mode in range(3):subprocess.run([str(exe),str(mode)],check=True,capture_output=True)
