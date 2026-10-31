# SPDX-License-Identifier: LGPL-3.0-or-later
import struct,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from check_pit_irq_config import check

def fixture(value=1):
 ident=b'\x7fELF\x01\x01\x01'+bytes(9)
 head=struct.pack('<HHIIIIIHHHHHH',2,189,1,0xffdc0050,52,0,0,52,32,1,0,0,0)
 table=bytearray(0x138);struct.pack_into('<I',table,44,value)
 ph=struct.pack('<8I',1,84,0xffdd8b68,0xffdd8b68,len(table),len(table),6,4)
 return ident+head+ph+table,'ffdd8b68 00000138 D XMicroblaze_ConfigTable'
class Tests(unittest.TestCase):
 def test_initial_value_not_live_claim(self):
  r=check(*fixture());self.assertEqual(r['field_address'],0xffdd8b94)
  for key in ['live_value_observed','later_writes_excluded','deployable','hardware_executed']:self.assertFalse(r[key])
 def test_changed_value_and_symbol_rejected(self):
  for v in [0,2,0xffffffff]:
   with self.assertRaises(ValueError):check(*fixture(v))
  d,s=fixture()
  for bad in [s+'\n'+s,s.replace('ffdd8b68','ffdd8b6c'),s.replace('00000138','00000134')]:
   with self.assertRaises(ValueError):check(d,bad)
