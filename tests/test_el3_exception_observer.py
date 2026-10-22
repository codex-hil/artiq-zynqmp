"""Exact vectors/fault path controls; LGPL-3.0-or-later."""
import struct
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from check_el3_exception_observer import BASE,SIZE,check,expected_payload


def fixture():
    data=bytearray(120+SIZE);data[:7]=b'\x7fELF\x02\x01\x01'
    struct.pack_into('<HHIQQQIHHHHHH',data,16,2,183,1,BASE+2048,64,0,0,64,56,1,0,0,0)
    struct.pack_into('<II6Q',data,64,1,5,120,BASE,BASE,SIZE,SIZE,4)
    data[120:]=expected_payload()
    return data


class ExceptionObserverTests(unittest.TestCase):
 def test_all_vector_slots_reach_handler(self):
  payload=expected_payload()
  for slot in range(16):
   offset=slot*128
   mov,branch=struct.unpack_from('<II',payload,offset)
   self.assertEqual((mov>>5)&0xffff,slot)
   self.assertEqual(offset+4+((branch&0x3ffffff)<<2),0x854)
   self.assertEqual(payload[offset+8:offset+128],bytes(120))
  self.assertFalse(check(fixture())['hardware_executed'])
 def test_changes_rejected(self):
  for offset in [0,4,15*128+4,2048,0x84c,0x874]:
   raw=fixture();raw[120+offset]^=1
   with self.assertRaises(ValueError):check(raw)
 def test_masking_store_or_writable_segment_rejected(self):
  for instruction in [0xd5034fdf,0xf9000000]:
   raw=fixture();struct.pack_into('<I',raw,120+2048,instruction)
   with self.assertRaises(ValueError):check(raw)
  raw=fixture();struct.pack_into('<I',raw,68,7)
  with self.assertRaises(ValueError):check(raw)


if __name__=='__main__':unittest.main()
