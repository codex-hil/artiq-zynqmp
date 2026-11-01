# SPDX-License-Identifier: LGPL-3.0-or-later
import re,struct,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from check_pit_fault_entry_link import check
from check_pmu_boundary_image import check as pmu_check
E=ROOT/'evidence/pit-fault-entry-link-offline-2026-11-01'
def fixture():return bytes.fromhex((E/'fixture.hex').read_text()),(E/'symbols.txt').read_text(),(E/'linked.dis').read_text()
class Tests(unittest.TestCase):
 def test_exact_fixture_never_pmu_runtime(self):
  d,s,t=fixture();r=check(d,s,t);self.assertFalse(r['deployable']);self.assertFalse(r['pmu_runtime_layout_qualified'])
  with self.assertRaises(ValueError):pmu_check(d,s)
 def test_every_linked_instruction_word_rejected(self):
  d,s,t=fixture();ph=struct.unpack_from('<8I',d,52);offset=ph[1]
  for index in range(64):
   bad=bytearray(d);bad[offset+index*4]^=1;pc=0x10000+index*4;word=struct.unpack_from('<I',bad,offset+index*4)[0]
   listing=re.sub(r'^\s*'+format(pc,'x')+r':\s+[0-9a-f]{8}\s+.*$',f'{pc:x}:\t{word:08x}\tor changed',t,flags=re.M)
   with self.assertRaises(ValueError):check(bytes(bad),s,listing)
 def test_changed_map_slot_and_stale_listing(self):
  d,s,t=fixture()
  for phoff in (52,84):
   for field in (2,3,4,5,6):
    bad=bytearray(d);pos=phoff+4*field;v=struct.unpack_from('<I',bad,pos)[0];struct.pack_into('<I',bad,pos,v+4)
    with self.assertRaises(ValueError):check(bytes(bad),s,t)
  with self.assertRaises(ValueError):check(d,s.replace('00020000 00000040 B pit_fault_entry_slot','00020008 00000040 B pit_fault_entry_slot'),t)
  with self.assertRaises(ValueError):check(d,s,t.replace('94608001','94608000',1))
