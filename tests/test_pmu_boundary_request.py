"""Actual C request publication/replay controls, no HW; LGPL-3.0-or-later."""
import subprocess,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class Tests(unittest.TestCase):
 def test_partial_replay_kind_and_sequence(self):
  text='''#include "telemetry.h"
#include <assert.h>
static void payload(uint32_t gen,uint64_t seq,uint32_t kind) {
 artiq_pmu_request.nonce_lo=123;artiq_pmu_request.nonce_hi=456;
 artiq_pmu_request.sequence_lo=(uint32_t)seq;artiq_pmu_request.sequence_hi=seq>>32;
 artiq_pmu_request.kind=kind;artiq_pmu_request.reserved=0;
 artiq_pmu_request.checksum=0x504d5551^gen^123^456^(uint32_t)seq^(uint32_t)(seq>>32)^kind;
}
int main(void) {
 payload(2,1,1);
 artiq_pmu_observe_boundary();assert(artiq_pmu_echo.generation==0);
 artiq_pmu_request.generation=1;artiq_pmu_observe_boundary();assert(artiq_pmu_echo.generation==0);
 artiq_pmu_request.generation=2;artiq_pmu_observe_boundary();assert(artiq_pmu_echo.generation==2);
 assert(artiq_pmu_echo.status==1 && artiq_pmu_echo.ack==0 && artiq_pmu_boundary.ack==0);
 payload(2,2,1);artiq_pmu_observe_boundary();assert(artiq_pmu_echo.sequence_lo==1);
 payload(4,1,1);artiq_pmu_request.generation=4;artiq_pmu_observe_boundary();assert(artiq_pmu_echo.generation==2);
 payload(6,2,2);artiq_pmu_request.generation=6;artiq_pmu_observe_boundary();assert(artiq_pmu_echo.generation==2);
 payload(8,2,1);artiq_pmu_request.checksum^=1;artiq_pmu_request.generation=8;
 artiq_pmu_observe_boundary();assert(artiq_pmu_echo.generation==2);
 payload(10,2,1);artiq_pmu_request.generation=10;artiq_pmu_observe_boundary();assert(artiq_pmu_echo.generation==10);
 assert(artiq_pmu_echo.nonce_lo==123 && artiq_pmu_echo.nonce_hi==456 && artiq_pmu_echo.sequence_lo==2 && artiq_pmu_echo.ack==0);
 return 0;
}
'''
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'test.c';p.write_text(text);exe=Path(tmp)/'test'
   subprocess.run(['gcc','-std=c11','-O2','-Wall','-Wextra','-Werror','-I'+str(ROOT/'diagnostics/ddr/pmu_boundary'),str(p),'-o',str(exe)],check=True)
   subprocess.run([str(exe)],check=True,timeout=5)
if __name__=='__main__':unittest.main()
