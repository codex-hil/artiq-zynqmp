# SPDX-License-Identifier: LGPL-3.0-or-later
import re,struct,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from check_pit_fault_slot import check,START,SIZE,STORAGE,BOUNDARIES
ARCHIVE=ROOT/'evidence/pit-fault-slot-minimal-offline-2026-10-31'
def fixture(offset=None,stale=False):
 text=(ARCHIVE/'pit_fault_store_audit.dis').read_text();rows={int(a,16):int(w,16) for a,w in re.findall(r'^([0-9a-f]+):\s+([0-9a-f]{8})',text,re.M)}
 if offset is not None:
  pc=START+offset;word=rows[pc]^1;rows[pc]=word
  if not stale:text=re.sub(r'^'+format(pc,'08x')+r':\s+[0-9a-f]{8}\s+.*$',f'{pc:08x}:\t{word:08x}\tor changed',text,flags=re.M)
 base=0xffdc0000;payload=bytearray(START+SIZE-base)
 for pc,w in rows.items():struct.pack_into('<I',payload,pc-base,w)
 ident=b'\x7fELF\x01\x01\x01'+bytes(9);head=struct.pack('<HHIIIIIHHHHHH',2,189,1,0xffdc0050,52,0,0,52,32,3,0,0,0)
 ph=b''.join(struct.pack('<8I',1,148,a,a,fs,ms,fl,4) for a,fs,ms,fl in [(base,len(payload),len(payload),7),(0xffdd8000,0,0x6df0,6),(0xffddf6e0,0,0x400,6)])
 sy=[f'{START:08x} {SIZE:08x} T pit_fault_store_audit']+[f'{a:08x} {z:08x} {k} {n}' for n,(a,z,k) in STORAGE.items()]+[f'{a:08x} B {n}' for n,a in BOUNDARIES.items()]+['ffdd96e0 00000020 b artiq_pmu_boundary']
 return ident+head+ph+payload,'\n'.join(sy),text
class Tests(unittest.TestCase):
 def test_exact_scoped_fixture(self):
  r=check(*fixture());self.assertEqual(r['instruction_words'],110);self.assertFalse(r['deployable']);self.assertFalse(r['mailbox']['pmu_ram_access_allowed'])
 def test_each_instruction_word(self):
  for offset in range(0,SIZE,4):
   with self.assertRaises(ValueError):check(*fixture(offset))
 def test_changed_storage_boundaries_and_listing(self):
  d,s,t=fixture()
  for n,(a,z,k) in STORAGE.items():
   line=f'{a:08x} {z:08x} {k} {n}'
   for bad in [s.replace(line,f'{a+4:08x} {z:08x} {k} {n}'),s+'\n'+line]:
    with self.assertRaises(ValueError):check(d,bad,t)
  for n,a in BOUNDARIES.items():
   with self.assertRaises(ValueError):check(d,s.replace(f'{a:08x} B {n}',f'{a+4:08x} B {n}'),t)
  with self.assertRaises(ValueError):check(*fixture(0,stale=True))
