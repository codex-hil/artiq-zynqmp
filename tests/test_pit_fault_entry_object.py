# SPDX-License-Identifier: LGPL-3.0-or-later
import struct,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from check_pit_fault_entry_object import check
DATA=bytes.fromhex((ROOT/'evidence/pit-fault-entry-object-offline-2026-11-01/object.hex').read_text())
def sections(data):
 h=struct.unpack_from('<HHIIIIIHHHHHH',data,16);return [struct.unpack_from('<10I',data,h[5]+40*i) for i in range(h[11])]
class Tests(unittest.TestCase):
 def test_exact_standalone_no_execution_claim(self):
  r=check(DATA);self.assertEqual(r['entry_functions'],2)
  for name in ['hardware_executed','deployable','uses_stack','calls','vector_sections','edr_read','linked_slot_address_qualified','reentry_excluded','sleep_proven','recovery_proven']:self.assertFalse(r[name])
 def test_every_entry_instruction_word_rejected(self):
  code=[s for s in sections(DATA) if s[1]==1 and s[2]==6 and s[5]==128]
  self.assertEqual(len(code),2)
  for s in code:
   for offset in range(0,128,4):
    bad=bytearray(DATA);bad[s[4]+offset]^=1
    with self.assertRaises(ValueError):check(bytes(bad))
 def test_slot_relocation_metadata_and_vectors_rejected(self):
  for s in sections(DATA):
   if s[1]==4:
    for offset in [0,4,8,12,16,20]:
     bad=bytearray(DATA);bad[s[4]+offset]^=1
     with self.assertRaises(ValueError):check(bytes(bad))
  bad=bytearray(DATA);pos=bad.find(b'.text.pit_fault_sw_entry_audit');self.assertGreater(pos,0);bad[pos:pos+7]=b'.vector'
  with self.assertRaises(ValueError):check(bytes(bad))
  for off in [16,18,24,28]:
   bad=bytearray(DATA);bad[off]^=1
   with self.assertRaises(ValueError):check(bytes(bad))
