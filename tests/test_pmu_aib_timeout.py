"""Host execution of unchanged AMD AIB enable body. LGPL-3.0-or-later."""
import subprocess,tempfile,unittest,hashlib
from pathlib import Path
VENDOR=Path('/home/codex-hil/.local/state/artiq-builds/pmu-sleep-guard-full-20261023/src/xpfw_aib.c')
class Tests(unittest.TestCase):
 def test_vendor_returns_after_ack_timeout(self):
  raw=VENDOR.read_text();body=raw[raw.index('void XPfw_AibEnable('):raw.index('/**\n * Disable AIB isolation')]
  shim='''#include <stdint.h>
#include <stdlib.h>
typedef uint32_t u32;
enum XPfwAib { RPU0=0, XPFW_AIB_FPD_TO_GPU=14, XPFW_AIB_ID_MAX=15 };
#define AIB_ACK_TIMEOUT 15U
#define LPD_SLCR_ISO_AIBAPB_REQ 1U
#define LPD_SLCR_ISO_AIBAXI_REQ 2U
#define LPD_SLCR_ISO_AIBAXI_ACK 3U
#define DEBUG_DETAILED 0
#define XPfw_Printf(...) ((void)0)
static u32 AibMask[15]={1};
static unsigned reads,sleeps,writes,ack;
static void XPfw_RMW32(u32 addr,u32 mask,u32 value) {if(addr!=2 || mask!=1 || value!=1)abort();writes++;}
static u32 XPfw_Read32(u32 addr) {if(addr!=3)abort();reads++;return ack;}
static void usleep(u32 n) {if(n!=10)abort();sleeps++;}
'''
  main='''int main(void) {
 ack=0;XPfw_AibEnable(RPU0);
 if(reads!=15 || sleeps!=15 || writes!=1)return 1;
 reads=sleeps=writes=0;ack=1;XPfw_AibEnable(RPU0);
 if(reads!=1 || sleeps || writes!=1)return 2;
 return 0;
}
'''
  with tempfile.TemporaryDirectory() as t:
   src=Path(t)/'aib.c';exe=Path(t)/'test';src.write_text(shim+body+main)
   subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror',str(src),'-o',str(exe)],check=True)
   subprocess.run([str(exe)],check=True,timeout=5)
if __name__=='__main__':unittest.main()
