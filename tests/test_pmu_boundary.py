"""Isolated PMU boundary hook, no HW; LGPL-3.0-or-later."""
import sys,tempfile,subprocess,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from stage_pmu_boundary import transform
class Tests(unittest.TestCase):
 def test_source_shape_and_second_patch_reject(self):
  p=Path('/home/codex-hil/.local/state/artiq-builds/fsbl-spd-dump-20261022/pmu-app/src/xpfw_core.c');text=p.read_text();out=transform(text)
  self.assertEqual(out.count('artiq_pmu_observe_boundary();'),1)
  self.assertLess(out.index('artiq_pmu_observe_boundary();'),out.index('mb_sleep();'))
  with self.assertRaises(ValueError):transform(out)
  with self.assertRaises(ValueError):transform(text.replace('do {','do{'))
 def test_real_c_cannot_ack_even_after_counter_wrap(self):
  text='''#include "telemetry.h"
int main(void) {
 artiq_pmu_boundary.ack=1;
 artiq_pmu_boundary.loop_count=0xffffffffU;
 artiq_pmu_observe_boundary();
 if (artiq_pmu_boundary.ack || artiq_pmu_boundary.unresolved!=0x7f || artiq_pmu_boundary.loop_count!=0 || artiq_pmu_boundary.sequence!=2) return 1;
 for (unsigned i=0;i<100;i++) artiq_pmu_observe_boundary();
 return artiq_pmu_boundary.ack || artiq_pmu_boundary.loop_count!=100 || artiq_pmu_boundary.sequence!=202;
}
'''
  with tempfile.TemporaryDirectory() as tmp:
   source=Path(tmp)/'test.c';source.write_text(text);exe=Path(tmp)/'test'
   subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-I'+str(ROOT/'diagnostics/ddr/pmu_boundary'),str(source),'-o',str(exe)],check=True)
   subprocess.run([str(exe)],check=True,timeout=5)
if __name__=='__main__':unittest.main()
