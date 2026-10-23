"""Allocated-space/recovery lifecycle controls, no HW; LGPL-3.0-or-later."""
import os,sys,tempfile,unittest,json,contextlib
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from check_hw_storage import RestoreReserve
from test_candidate_runtime_hw import lifecycle
class Tests(unittest.TestCase):
 def test_real_blocks_unlinked_deduplicated_and_released(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)
   with RestoreReserve({'first':p,'same_disk':p/'future'},amount=1024*1024) as r:
    self.assertEqual(len(r.fds),1);self.assertGreaterEqual(os.fstat(r.fds[0]).st_blocks*512,1024*1024)
    self.assertEqual(list(p.iterdir()),[]);fd=r.fds[0]
    self.assertEqual(r.report()['status'],'ALLOCATED')
    r.release();self.assertEqual(r.report()['status'],'RELEASED_FOR_RESTORATION')
    with self.assertRaises(OSError):os.fstat(fd)
 def test_partial_allocation_failure_cleans_all_descriptors(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp);real=os.posix_fallocate;calls=[];fds=[]
   def allocate(fd,offset,size):
    fds.append(fd);calls.append(size)
    if len(calls)==2:raise OSError('simulated disk full')
    real(fd,offset,size)
   r=RestoreReserve({'a':p,'b':p},amount=1024*1024)
   with patch.object(RestoreReserve,'device',side_effect=[1,2]),patch('check_hw_storage.os.posix_fallocate',side_effect=allocate):
    with self.assertRaises(OSError):r.__enter__()
   self.assertTrue(r.released);self.assertEqual(r.fds,[]);self.assertEqual(list(p.iterdir()),[])
   for fd in fds:
    with self.assertRaises(OSError):os.fstat(fd)
 def test_reserve_released_before_restoration_after_interrupt(self):
  with tempfile.TemporaryDirectory() as tmp:
   with RestoreReserve({'a':Path(tmp)},amount=1024*1024) as r:
    calls=[]
    def cycle(phase):
     calls.append(phase)
     if phase=='candidate':
      self.assertFalse(r.released);raise KeyboardInterrupt()
     self.assertTrue(r.released);return 'restored'
    result=lifecycle(cycle,before_restore=r.release)
    self.assertEqual(calls,['candidate','restore']);self.assertEqual(result['restoration'],'PASS');self.assertEqual(result['status'],'FAIL')
 def test_release_failure_still_attempts_restore(self):
  calls=[]
  def before():raise RuntimeError('release error')
  r=lifecycle(lambda phase:calls.append(phase) or phase,before_restore=before)
  self.assertEqual(calls,['candidate','restore']);self.assertEqual(r['restoration'],'PASS');self.assertEqual(r['status'],'FAIL')
 def test_parent_reservation_failure_prevents_hardware_subprocess(self):
  import test_candidate_runtime_hw as parent
  with tempfile.TemporaryDirectory() as tmp:
   manifest=Path(tmp)/'inputs.json';manifest.write_text('{}')
   args=['test','--manifest',str(manifest),'--output',str(Path(tmp)/'out'),'--execute','--server','unused','--port','unused','--interface','unused']
   with patch.object(sys,'argv',args),patch.object(parent,'preflight',return_value={}),patch.object(parent,'require_runtime_space',return_value={}),patch.object(parent,'lease',return_value=contextlib.nullcontext(object())),patch.object(RestoreReserve,'__enter__',side_effect=RuntimeError('reserve unavailable')),patch.object(parent,'bounded') as hardware:
    with self.assertRaisesRegex(RuntimeError,'reserve unavailable'):parent.main()
    hardware.assert_not_called()
 def test_insufficient_headroom_allocates_nothing(self):
  with tempfile.TemporaryDirectory() as tmp:
   r=RestoreReserve({'a':Path(tmp)},amount=2**63)
   with self.assertRaises(RuntimeError):r.__enter__()
   self.assertTrue(r.released);self.assertEqual(r.fds,[])
if __name__=='__main__':unittest.main()
