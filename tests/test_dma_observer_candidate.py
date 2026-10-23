"""Optional candidate preflight and restoration controls; LGPL-3.0-or-later."""
import copy,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from test_candidate_runtime_hw import preflight,lifecycle
from dma_observer_candidate import verify_snapshot
PLAN=ROOT/'evidence/dma-observer-short-workload-2026-10-23/inputs.json'
class Tests(unittest.TestCase):
 def test_actual_build_and_stale_pin_rejections(self):
  m=json.loads(PLAN.read_text());preflight(m)
  for what in ['build','script','missing','map']:
   bad=copy.deepcopy(m)
   if what=='build':bad['dma_observer']['build_inputs']['sha256']='0'*64
   elif what=='script':bad['dma_observer']['script_sha256']['scripts/probe_dma_observer.tcl']='0'*64
   elif what=='missing':del bad['dma_observer']['script_sha256']['scripts/check_dma_observer_snapshot.py']
   else:bad['files']['candidate_csr']=bad['files']['candidate_pl']
   with self.assertRaises(ValueError):preflight(bad)
 def frame(self,count=0,flags=0):
  return 'DMA_OBSERVER_BEGIN\n'+''.join(f'DMA_OBSERVER {s} 0x{a:08x} 0x{v:08x}\n' for s in range(2) for a,v in [(0xa0003000,count),(0xa0003004,flags)])+'DMA_OBSERVER_END\n'
 def test_zero_not_admission_and_failures_restore(self):
  self.assertFalse(verify_snapshot(self.frame())['destructive_test_allowed'])
  for bad in [self.frame(count=1),self.frame(flags=1),self.frame(flags=2),self.frame(flags=4),'incomplete']:
   calls=[]
   def cycle(which):
    calls.append(which)
    if which=='candidate':verify_snapshot(bad)
    return 'baseline'
   r=lifecycle(cycle)
   self.assertEqual(r['status'],'FAIL');self.assertEqual(r['restoration'],'PASS')
   self.assertEqual(calls,['candidate','restore'])
if __name__=='__main__':unittest.main()
