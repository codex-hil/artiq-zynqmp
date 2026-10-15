"""Execute actual firmware reset helpers against MMIO fault injection; LGPL-3.0-or-later."""
from pathlib import Path
import subprocess
import tempfile
import unittest

class ResetBackendTests(unittest.TestCase):
    def test_completion_faults_and_phy_preservation(self):
        header=Path(__file__).resolve().parents[1]/'diagnostics/drtio/aux_protocol'
        source=r'''
#include <stdint.h>
#include <assert.h>
enum { REG_AUX_IN_RESET,REG_AUX_RX_UP,REG_AUX_RT_REPLY_FAULT,
 REG_AUX_PHY_RESET_REQUEST,REG_AUX_PHY_RESET_APPLIED,REG_AUX_TSC_LOAD_COUNT,
 REG_AUX_RTIO_RESET_REQUEST,REG_AUX_RTIO_RESET_APPLIED,REG_AUX_RTIO_ERROR_FLAGS };
static uint32_t regs[9];static int stuck, change_tsc, lose_clock, phy_writes, held;
static uint32_t rd(uintptr_t a){return regs[a];}
static void wr(uintptr_t a,uint32_t v){
 regs[a]=v;
 if(a==REG_AUX_PHY_RESET_REQUEST){phy_writes++;regs[REG_AUX_PHY_RESET_APPLIED]=v;}
 if(a==REG_AUX_RTIO_RESET_REQUEST && !stuck)regs[REG_AUX_RTIO_RESET_APPLIED]=v;
}
static int wait(uintptr_t a,uint32_t v){return rd(a)==v?0:-1;}
static void usleep(unsigned n){held+=n;if(change_tsc)regs[REG_AUX_TSC_LOAD_COUNT]++;if(lose_clock)regs[REG_AUX_RX_UP]=0;}
#include "reset_backend.h"
static void init(void){for(int i=0;i<9;i++)regs[i]=0;regs[REG_AUX_RX_UP]=1;regs[REG_AUX_TSC_LOAD_COUNT]=1;stuck=change_tsc=lose_clock=phy_writes=held=0;}
int main(void){
 init();assert(reset_backend()==0);assert(held>=100);assert(!phy_writes);assert(regs[REG_AUX_TSC_LOAD_COUNT]==1);assert(!regs[REG_AUX_RTIO_RESET_REQUEST]);
 init();stuck=1;assert(reset_backend()<0);
 init();change_tsc=1;assert(reset_backend()<0);
 init();lose_clock=1;assert(reset_backend()<0);
 init();regs[REG_AUX_RT_REPLY_FAULT]=1;assert(reset_backend()<0);assert(!held);
 init();regs[REG_AUX_PHY_RESET_APPLIED]=1;assert(reset_backend()<0);
 init();regs[REG_AUX_RTIO_ERROR_FLAGS]=1;assert(reset_backend()<0);
 init();assert(release_backend()<0); /* cold reset not proven */
 init();regs[REG_AUX_RTIO_RESET_REQUEST]=regs[REG_AUX_RTIO_RESET_APPLIED]=1;
 regs[REG_AUX_PHY_RESET_REQUEST]=regs[REG_AUX_PHY_RESET_APPLIED]=1;
 assert(release_backend()==0);assert(phy_writes==1);assert(!regs[REG_AUX_RTIO_RESET_APPLIED]);
 return 0;
}'''
        with tempfile.TemporaryDirectory() as tmp:
            c=Path(tmp)/'test.c';c.write_text(source);exe=Path(tmp)/'test'
            subprocess.run(['cc','-std=c99','-Wall','-Wextra','-Werror','-I'+str(header),str(c),'-o',str(exe)],check=True,timeout=30)
            subprocess.run([str(exe)],check=True,timeout=5)
