# SPDX-License-Identifier: LGPL-3.0-or-later
import hashlib,struct,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'diagnostics/ddr'))
from pit_session_correlation import Session
from pit_terminal_receipt import FORMAT,MAGIC
from pit_sleep_observation import ADDRESS
IMAGE='12'*32
SAMPLES=struct.pack('<IIQ8I',1,1,7,*range(8))
def terminal(nonce=7,image=IMAGE,samples=SAMPLES,status=4):
 return FORMAT.pack(1,MAGIC,1,status,nonce,0x80000104,0x80000104,bytes.fromhex(image),hashlib.sha256(samples).digest())
def sample():return dict(version=1,nonce=7,address=ADDRESS,return_code=0,value=0x10000)
class Tests(unittest.TestCase):
 def test_complete_correlation_never_admits(self):
  s=Session(7,IMAGE);s.observe(sample());r=s.terminal(terminal(),terminal(),SAMPLES)
  self.assertTrue(r['terminal_content_bound']);self.assertEqual(r['terminal_status'],'CAPTURE_COMPLETE')
  for k in ['origin_authenticated','sleep_proven','pmu_ram_access_allowed','deployable','hardware_executed','destructive_test_allowed']:self.assertIs(r[k],False)
 def test_mixed_session_image_sample_and_torn_bytes_poison(self):
  for first,second,samples in [(terminal(8),terminal(8),SAMPLES),(terminal(image='34'*32),terminal(image='34'*32),SAMPLES),(terminal(),terminal(),bytes(48)),(terminal(),terminal()[:-1],SAMPLES)]:
   s=Session(7,IMAGE)
   with self.assertRaises(ValueError):s.terminal(first,second,samples)
   self.assertTrue(s.observe(sample())['lifetime']['invalidated'])
   with self.assertRaises(ValueError):s.terminal(terminal(),terminal(),SAMPLES)
 def test_valid_receipt_and_late_sleep_cannot_revive_events(self):
  for event in ['wake','reset','debug','exception','transport_unknown','ownership_lost']:
   s=Session(7,IMAGE);s.event(event);s.terminal(terminal(),terminal(),SAMPLES);r=s.observe(sample())
   self.assertTrue(r['lifetime']['invalidated']);self.assertEqual(r['lifetime']['first_invalidation'],event)
   r['lifetime']['invalidated']=False;self.assertTrue(s.report()['lifetime']['invalidated'])
 def test_duplicate_closed_and_error_receipt_controls(self):
  for status in [1,2,3]:
   s=Session(7,IMAGE);d=terminal(status=status);r=s.terminal(d,d,SAMPLES);self.assertTrue(r['terminal_content_bound']);self.assertFalse(r['sleep_proven'])
   with self.assertRaises(ValueError):s.terminal(d,d,SAMPLES)
   self.assertTrue(s.report()['lifetime']['invalidated'])
  s=Session(7,IMAGE);s.close()
  with self.assertRaises(ValueError):s.terminal(terminal(),terminal(),SAMPLES)
  for image in [True,'0'*64,'AB'*32,'']:
   with self.assertRaises(ValueError):Session(7,image)
if __name__=='__main__':unittest.main()
