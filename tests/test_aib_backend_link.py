"""Exact actual ELF table/assignment mutation controls. LGPL-3.0-or-later."""
import sys,unittest,struct
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from check_aib_backend_link import check
B=Path('/home/codex-hil/.local/state/artiq-builds/aib-backend-audit-link-20261027')
def offset(raw,addr):
 off=struct.unpack_from('<I',raw,28)[0];step,count=struct.unpack_from('<HH',raw,42)
 for i in range(count):
  s=struct.unpack_from('<8I',raw,off+i*step)
  if s[0]==1 and s[2]<=addr<s[2]+s[4]:return s[1]+addr-s[2]
 raise ValueError('Unmapped')
class Tests(unittest.TestCase):
 def test_actual_and_mutations(self):
  raw=(B/'audit-only.elf').read_bytes();symbols=(B/'symbols.txt').read_text()
  self.assertFalse(check(raw,symbols)['destructive_test_allowed'])
  for addr in [0xffdd42c4,0xffdcfce0,0xffdcfd00]:
   bad=bytearray(raw);bad[offset(raw,addr)]^=4
   with self.assertRaises(ValueError):check(bad,symbols)
if __name__=='__main__':unittest.main()
