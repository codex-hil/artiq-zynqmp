"""Subprocess startup/cleanup and marker controls; LGPL-3.0-or-later."""
import sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from run_dma_observer_active import run_workload,validate_workload
class Tests(unittest.TestCase):
 def test_workload_and_sampler_order(self):
  command=[sys.executable,'-u','-c','import time;print("DMA_OBSERVER_LOAD 1",flush=True);time.sleep(.3);print("DMA_OBSERVER_LOAD 2",flush=True)']
  with tempfile.TemporaryDirectory() as tmp:
   r=run_workload(command,Path(tmp)/'log',lambda:{'status':'INCONCLUSIVE_NO_NONZERO_SAMPLE'})
   self.assertTrue(r['workload_active_through_sample_end']);self.assertFalse(r['destructive_test_allowed'])
 def test_no_start_timeout_and_sampler_error(self):
  for program,sampler in [('import time;time.sleep(10)',lambda:{}),('print("no marker")',lambda:{}),('import time;print("DMA_OBSERVER_LOAD 1",flush=True);time.sleep(10)',lambda:(_ for _ in ()).throw(ValueError('bad sample')))]:
   with tempfile.TemporaryDirectory() as tmp:
    with self.assertRaises((ValueError,TimeoutError)):
     run_workload([sys.executable,'-u','-c',program],Path(tmp)/'log',sampler,ready_timeout=.1,total_timeout=1)
 def test_completed_samples_survive_later_workload_failure(self):
  progress={}
  program='import time,sys;print("DMA_OBSERVER_LOAD 1",flush=True);time.sleep(.2);sys.exit(1)'
  with tempfile.TemporaryDirectory() as tmp:
   with self.assertRaises(ValueError):
    run_workload([sys.executable,'-u','-c',program],Path(tmp)/'log',lambda:{'max_outstanding':27},progress=progress)
  self.assertEqual(progress['sampling']['max_outstanding'],27)
  self.assertEqual(progress['workload_returncode'],1)
 def test_phase_validation(self):
  for bad in ['', 'DMA_OBSERVER_LOAD 1\n', 'DMA_OBSERVER_LOAD 2\nDMA_OBSERVER_LOAD 1\n']:
   with self.assertRaises(ValueError):validate_workload(bad)
if __name__=='__main__':unittest.main()
