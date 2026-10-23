"""Actual C non-returning lab guard with offline host backend; LGPL-3.0-or-later."""
import subprocess,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class Tests(unittest.TestCase):
 def test_guard_enters_without_ack_preserves_ee_and_never_returns(self):
  source='''#define _GNU_SOURCE
#define ARTIQ_PMU_LAB_GUARD 1
#define ARTIQ_PMU_GUARD_HOST_TEST 1
#include "telemetry.h"
#include <sys/uio.h>
#include <sys/wait.h>
#include <signal.h>
#include <unistd.h>
#include <stdlib.h>
static uint32_t fake_msr=0x102;
static int bad;
uint32_t artiq_guard_test_msr(void) {return fake_msr;}
void artiq_guard_test_disable_irq(void) {fake_msr=bad ? 0 : 0x100;}
int main(int argc,char **argv) {
 (void)argv;bad=argc>1;
 pid_t child=fork();if(child<0)return 10;
 if(!child) {
  artiq_pmu_request.nonce_lo=123;artiq_pmu_request.nonce_hi=456;
  artiq_pmu_request.sequence_lo=1;artiq_pmu_request.sequence_hi=0;
  artiq_pmu_request.kind=2;artiq_pmu_request.reserved=0;
  artiq_pmu_request.checksum=0x504d5551^2^123^456^1^2;
  artiq_pmu_request.generation=2;
  artiq_pmu_observe_boundary();_exit(11);
 }
 struct artiq_pmu_guard_record snapshot={0};int got=0,exited=0;
 for(unsigned i=0;i<100;i++) {
  struct iovec local={&snapshot,sizeof snapshot},remote={(void*)&artiq_pmu_guard,sizeof snapshot};
  if(process_vm_readv(child,&local,1,&remote,1,0)==sizeof snapshot && snapshot.generation==2) {got=1;break;}
  if(waitpid(child,0,WNOHANG)==child) {exited=1;break;}
  usleep(10000);
 }
 int alive=!exited && waitpid(child,0,WNOHANG)==0;
 if(alive) {kill(child,SIGKILL);waitpid(child,0,0);}
 if(!got || !alive)return 12;
 if(snapshot.state!=(bad?3U:2U) || snapshot.ack || snapshot.unresolved!=0x7f)return 13;
 if(snapshot.msr_before!=0x102 || snapshot.msr_after!=(bad?0U:0x100U))return 14;
 if(snapshot.nonce_lo!=123 || snapshot.nonce_hi!=456 || snapshot.sequence_lo!=1 || snapshot.kind!=2)return 15;
 return 0;
}
'''
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'test.c';p.write_text(source);exe=Path(tmp)/'test'
   subprocess.run(['gcc','-std=c11','-O2','-Wall','-Wextra','-Werror','-I'+str(ROOT/'diagnostics/ddr/pmu_boundary'),str(p),'-o',str(exe)],check=True)
   subprocess.run([str(exe)],check=True,timeout=5)
   subprocess.run([str(exe),'bad-msr'],check=True,timeout=5)
if __name__=='__main__':unittest.main()
