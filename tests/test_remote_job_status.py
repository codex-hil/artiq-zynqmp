"""Stale service status controls; LGPL-3.0-or-later."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from remote_rtio_build import classify_status,service_command
class Tests(unittest.TestCase):
 def test_incomplete_and_terminal(self):
  for state in ['RUNNING','WAITING_FOR_BUILD_LOCK']:
   self.assertEqual(classify_status(state,'inactive',None)['status'],'INCOMPLETE_SERVICE_INACTIVE')
   self.assertEqual(classify_status(state,'active',None)['status'],state)
  self.assertEqual(classify_status('RUNNING','inactive',0)['status'],'FINISHED')
  self.assertEqual(classify_status('RUNNING','inactive',1)['status'],'FAILED')
 def test_wait_keeps_session_and_bounds_service(self):
  m={'job':'example','remote':'/srv/nvme-fast-1/vivado-work/example'}
  ordinary=service_command(m)
  waiting=service_command(m,True)
  self.assertNotIn('--wait',ordinary)
  self.assertIn('--wait',waiting)
  self.assertIn('--property=RuntimeMaxSec=10800',waiting)
  self.assertEqual(waiting[-2:],['/bin/bash',m['remote']+'/run.sh'])
if __name__=='__main__':unittest.main()
