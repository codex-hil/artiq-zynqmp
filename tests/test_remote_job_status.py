"""Stale service status controls; LGPL-3.0-or-later."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from remote_rtio_build import classify_status
class Tests(unittest.TestCase):
 def test_incomplete_and_terminal(self):
  for state in ['RUNNING','WAITING_FOR_BUILD_LOCK']:
   self.assertEqual(classify_status(state,'inactive',None)['status'],'INCOMPLETE_SERVICE_INACTIVE')
   self.assertEqual(classify_status(state,'active',None)['status'],state)
  self.assertEqual(classify_status('RUNNING','inactive',0)['status'],'FINISHED')
  self.assertEqual(classify_status('RUNNING','inactive',1)['status'],'FAILED')
if __name__=='__main__':unittest.main()
