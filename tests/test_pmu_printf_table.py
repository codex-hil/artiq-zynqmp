"""Actual ELF table and negative controls. SPDX-License-Identifier: LGPL-3.0-or-later"""
import sys,unittest,struct
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from check_pmu_printf_table import check,mapped
ELF=Path('/home/codex-hil/.local/state/artiq-builds/pmu-sleep-guard-full-20261023/pmufw.elf')
class Tests(unittest.TestCase):
 def test_actual_and_corrupt_targets(self):
  raw=ELF.read_bytes();m=check(raw);self.assertEqual(len(m['entries']),22);self.assertFalse(m['destructive_test_allowed'])
  table=mapped(raw,0xffdd35d0,88);offset=raw.index(table)
  for target in [0x80000000,0xffdcc811,0xffdccbc0]:
   bad=bytearray(raw);struct.pack_into('<I',bad,offset,target)
   with self.assertRaises(ValueError):check(bad)
 def test_instruction_mutation_and_unmapped(self):
  raw=ELF.read_bytes();off=struct.unpack_from('<I',raw,28)[0];ents,count=struct.unpack_from('<HH',raw,42)
  segments=[struct.unpack_from('<8I',raw,off+i*ents) for i in range(count)]
  seg=next(s for s in segments if s[0]==1 and s[2]<=0xffdcc9ec<s[2]+s[4])
  pos=seg[1]+0xffdcc9ec-seg[2];bad=bytearray(raw);bad[pos]^=1
  with self.assertRaises(ValueError):check(bad)
  with self.assertRaises(ValueError):mapped(raw,0x80000000,4)
if __name__=='__main__':unittest.main()
