# SPDX-License-Identifier: LGPL-3.0-or-later
import sys,unittest,re,struct
from pathlib import Path
from unittest.mock import patch
from test_pit_digest_root_flow import fixture as original_fixture
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pit_digest_stack_audit as audit
def fixture():
 data,symbols,text=original_fixture()
 fence=(Path(__file__).resolve().parents[1]/'evidence/pit-digest-stack-offline-2026-10-31/fence.dis').read_text()
 data=bytearray(data)
 for pc,word in re.findall(r'^([0-9a-f]+):\s+([0-9a-f]{8})',fence,re.M):struct.pack_into('<I',data,148+int(pc,16)-0xffdc0000,int(word,16))
 return bytes(data),symbols+'\nffdcc778 00000018 t fence',text+'\n'+fence
class Tests(unittest.TestCase):
 def test_exact_artifact_conditional_normal_path(self):
  r=audit.audit(*fixture());self.assertEqual(r['normal_peak_bytes'],792)
  self.assertEqual(r['peak_path'],['pit_digest_root_audit','pit_capture_digest','pit_sample_sha256','swap'])
  self.assertEqual(len(r['graph']),28);self.assertFalse(r['deployable']);self.assertTrue(r['indirect_binding_assumptions'])
 def test_missing_binding_or_changed_frame_refused(self):
  bad=dict(audit.INDIRECT);bad.pop(('pit_ro_read','r3'))
  with patch.object(audit,'INDIRECT',bad):
   with self.assertRaisesRegex(ValueError,'indirect'):audit.audit(*fixture())
  bad=dict(audit.FRAMES);bad['pit_capture_digest']=152
  with patch.object(audit,'FRAMES',bad):
   with self.assertRaisesRegex(ValueError,'allocation'):audit.audit(*fixture())
 def test_cycles_missing_frames_and_nonaccumulating_sequential_calls(self):
  self.assertEqual(audit.max_path({'r':10,'a':20,'b':30},{'r':['a','b'],'a':[],'b':[]},'r')[0],40)
  for frames,graph in [({'r':1},{'r':['r']}),({'r':1},{'r':['unknown']}),({'r':-1},{'r':[]})]:
   with self.assertRaises(ValueError):audit.max_path(frames,graph,'r')
 def test_each_additional_fence_word_rejected(self):
  for offset in range(0,24,4):
   data,symbols,text=fixture();data=bytearray(data);pc=0xffdcc778+offset
   word=struct.unpack_from('<I',data,148+pc-0xffdc0000)[0]^1
   struct.pack_into('<I',data,148+pc-0xffdc0000,word)
   text=re.sub(r'^'+format(pc,'08x')+r':\s+[0-9a-f]{8}\s+.*$',f'{pc:08x}:\t{word:08x}\tor changed',text,flags=re.M)
   with self.assertRaisesRegex(ValueError,'fence'):audit.audit(bytes(data),symbols,text)
