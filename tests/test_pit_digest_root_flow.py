# SPDX-License-Identifier: LGPL-3.0-or-later
import json,re,struct,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from check_pit_digest_root_flow import check,PINS,STORAGE_PINS,CONSTANT_PIN
ARCHIVE=ROOT/'evidence/pit-digest-root-offline-2026-10-31'
def fixture(mutation=None,constant=None,stale=False):
 texts={n:(ARCHIVE/(n+'.dis')).read_text() for n in PINS}
 rows={int(a,16):int(w,16) for t in texts.values() for a,w in re.findall(r'^([0-9a-f]+):\s+([0-9a-f]{8})',t,re.M)}
 if mutation:
  name,offset=mutation;pc=PINS[name][0]+offset;word=rows[pc]^1;rows[pc]=word
  if not stale:texts[name]=re.sub(r'^'+format(pc,'08x')+r':\s+[0-9a-f]{8}\s+.*$',f'{pc:08x}:\t{word:08x}\tor synthetic',texts[name],flags=re.M)
 a,z,_=CONSTANT_PIN;constants=bytearray.fromhex(json.loads((ARCHIVE/'sha-constants.json').read_text())['hex'])
 if constant is not None:constants[constant]^=1
 base=0xffdc0000;payload=bytearray(max(max(rows)+4,a+z)-base)
 for pc,w in rows.items():struct.pack_into('<I',payload,pc-base,w)
 payload[a-base:a-base+z]=constants
 ident=b'\x7fELF\x01\x01\x01'+bytes(9);header=struct.pack('<HHIIIIIHHHHHH',2,189,1,0xffdc0050,52,0,0,52,32,3,0,0,0)
 ph=b''.join(struct.pack('<8I',1,148,addr,addr,fs,ms,flags,4) for addr,fs,ms,flags in [(base,len(payload),len(payload),7),(0xffdd8000,0,0x75e8,6),(0xffddf6e0,0,0x400,6)])
 symbols=[f'{x:08x} {size:08x} T {n}' for n,(x,size,_) in PINS.items()]+[f'{x:08x} {size:08x} {kind} {n}' for n,(x,size,kind) in STORAGE_PINS.items()]
 symbols += [f'{a:08x} {z:08x} r k','ffdd9e00 B __bss_start','ffdd9f20 00000020 b artiq_pmu_boundary','ffdddcc8 B __bss_end','ffdde5e4 B _stack_end','ffddf5e8 B _stack']
 return ident+header+ph+payload,'\n'.join(symbols),'\n'.join(texts.values())
class Tests(unittest.TestCase):
 def test_exact_reviewed_artifact_scopes(self):
  r=check(*fixture());self.assertEqual(len(r['functions']),29);self.assertFalse(r['deployable']);self.assertFalse(r['mailbox']['pmu_ram_access_allowed'])
 def test_every_scoped_instruction_mutation(self):
  for n,(a,z,h) in PINS.items():
   for offset in range(0,z,4):
    with self.assertRaises(ValueError,msg=f'{n}+{offset}'):check(*fixture((n,offset)))
 def test_each_constant_word_mutation(self):
  for offset in range(0,256,4):
   with self.assertRaises(ValueError):check(*fixture(constant=offset))
 def test_storage_listing_constant_range_and_duplicates(self):
  d,s,t=fixture()
  for n,(a,z,kind) in STORAGE_PINS.items():
   with self.assertRaises(ValueError):check(d,s.replace(f'{a:08x} {z:08x} {kind} {n}',f'{a+4:08x} {z:08x} {kind} {n}'),t)
  a,z,_=CONSTANT_PIN;line=f'{a:08x} {z:08x} r k'
  for bad in [s+'\n'+line,s.replace(line,f'{a+4:08x} {z:08x} r k')]:
   with self.assertRaises(ValueError):check(d,bad,t)
  with self.assertRaises(ValueError):check(*fixture(('pit_digest_root_audit',0),stale=True))
