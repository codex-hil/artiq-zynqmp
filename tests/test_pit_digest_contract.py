# SPDX-License-Identifier: LGPL-3.0-or-later
import hashlib,struct,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from pit_digest_contract import sample_digest,image_digest,digest_words
class Tests(unittest.TestCase):
 def test_exact_record_bytes_and_session(self):
  record=struct.pack('<IIQ8I',1,1,0x1122334455667788,*range(8))
  digest=sample_digest(record,0x1122334455667788)
  self.assertEqual(digest,hashlib.sha256(record).digest())
  self.assertEqual(struct.pack('<8I',*digest_words(digest)),digest)
  for i in range(16,48):
   changed=bytearray(record);changed[i]^=1
   self.assertNotEqual(sample_digest(bytes(changed),0x1122334455667788),digest)
  for bad in [record[:-1],record+b'\0',bytearray(record),record[4:],b'']:
   with self.assertRaises(ValueError):sample_digest(bad,0x1122334455667788)
  for n in [True,0,-1,2**64,123]:
   with self.assertRaises(ValueError):sample_digest(record,n)
  for offset in [0,4,8]:
   bad=bytearray(record);bad[offset]^=1
   with self.assertRaises(ValueError):sample_digest(bytes(bad),0x1122334455667788)
 def test_artifact_identity_and_word_encoding(self):
  self.assertEqual(image_digest(b'abc').hex(),'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad')
  self.assertEqual(digest_words(bytes(range(32)))[0],0x03020100)
  self.assertNotEqual(image_digest(b'abc'),image_digest(b'abc\0'))
  for bad in [b'',bytearray(b'abc'),'abc']:
   with self.assertRaises(ValueError):image_digest(bad)
  for bad in [bytes(31),bytes(33),bytearray(32)]:
   with self.assertRaises(ValueError):digest_words(bad)
