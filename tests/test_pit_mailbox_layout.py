# SPDX-License-Identifier: LGPL-3.0-or-later
import struct,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from check_pit_mailbox_layout import check

def fixture():
 ident=b'\x7fELF\x01\x01\x01'+bytes(9)
 header=struct.pack('<HHIIIIIHHHHHH',2,189,1,0xffdc0050,52,0,0,52,32,3,0,0,0)
 ph=b''.join(struct.pack('<8I',1,148,addr,addr,0,size,flags,4) for addr,size,flags in [(0xffdc0000,0x100,7),(0xffdd0000,0x1000,6),(0xffddf6e0,0x400,6)])
 symbols='\n'.join(['ffdd0000 B __bss_start','ffdd0100 00000020 b artiq_pmu_boundary','ffdd0200 00000090 B pit_mailbox_audit','ffdd0300 B __bss_end','ffdd0400 B _stack_end','ffdd1000 B _stack'])
 return ident+header+ph,symbols
class Tests(unittest.TestCase):
 def test_symbol_derived_subrecords_never_authorize(self):
  r=check(*fixture());self.assertEqual(r['terminal']['start'],'0xffdd0230');self.assertFalse(r['pmu_ram_access_allowed']);self.assertIn('NOT_EXCLUDED',r['heap_scope'])
 def test_wrong_size_alignment_bss_type_and_missing_bounds(self):
  data,text=fixture()
  for bad in [text.replace('00000090','0000008c'),text.replace('ffdd0200','ffdd0204'),text.replace(' B pit_mailbox_audit',' D pit_mailbox_audit'),text.replace('ffdd0300 B __bss_end','ffdd0270 B __bss_end'),text.replace(' B __bss_start',' B wrong')]:
   with self.assertRaises(ValueError):check(data,bad)
 def test_sized_owner_stack_heap_and_duplicate_overlap(self):
  data,text=fixture()
  for bad in [text+'\nffdd0220 00000004 b another_owner',text.replace('ffdd0400 B _stack_end','ffdd0260 B _stack_end'),text+'\nffdd0100 B _heap_start\nffdd0250 B _heap_end',text+'\nffdd0100 B _heap_start',text+'\nffdd0200 00000090 B pit_mailbox_audit']:
   with self.assertRaises(ValueError):check(data,bad)
 def test_initialized_or_readonly_segment_rejected(self):
  data,text=fixture()
  changed=bytearray(data);struct.pack_into('<I',changed,52+32+24,4)
  with self.assertRaises(ValueError):check(bytes(changed),text)
if __name__=='__main__':unittest.main()
