# SPDX-License-Identifier: LGPL-3.0-or-later
import re,struct,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from check_pit_mmio_word_flow import check,PINS

def fixture(mutation=None,stale=False):
 texts={}
 for n in PINS:
  folder='pit-capture-word-init-offline-2026-10-30'
  texts[n]=(ROOT/'evidence'/folder/(n+'.dis')).read_text()
 rows={int(a,16):int(w,16) for text in texts.values() for a,w in re.findall(r'^([0-9a-f]+):\s+([0-9a-f]{8})',text,re.M)}
 if mutation:
  name,offset,word=mutation;pc=PINS[name][0]+offset;assert pc in rows;rows[pc]=word
  if not stale:texts[name]=re.sub(r'^'+format(pc,'08x')+r':\s+[0-9a-f]{8}\s+.*$',f'{pc:08x}:\t{word:08x}\tor synthetic',texts[name],flags=re.M)
 base=min(rows);payload=bytearray(max(rows)-base+4)
 for pc,word in rows.items():struct.pack_into('<I',payload,pc-base,word)
 symbols='\n'.join(f'{start:08x} {size:08x} T {n}' for n,(start,size,_) in PINS.items())
 header=b'\x7fELF\x01\x01\x01'+bytes(9)+struct.pack('<HHIIIIIHHHHHH',2,189,1,0xffdc0050,52,0,0,52,32,1,0,0,0)
 ph=struct.pack('<8I',1,84,base,base,len(payload),len(payload),7,4)
 return header+ph+payload,symbols,'\n'.join(texts.values())

class Tests(unittest.TestCase):
 def test_reviewed_bodies(self):
  result=check(*fixture());self.assertEqual(len(result['functions']),8);self.assertFalse(result['deployable']);self.assertFalse(result['external_callback_paths_qualified'])
 def test_consistent_binding_address_budget_output_mutants(self):
  mutations=[('pit_mmio_composition_audit',0x28,0x80000000),('pit_mmio_composition_audit',0x34,0x80000000),('pit_mmio_composition_audit',0x40,0x80000000),('pit_mmio_composition_audit',0x48,0x80000000),('pit_mmio_composition_audit',0x50,0x80000000),('pit_mmio_composition_audit',0x58,0x30a0bfb4),('pit_mmio_composition_audit',0x64,0x80000000),('pit_mmio_read',0x18,0xb000ffd5),('pit_mmio_read',0x1c,0xa8660060),('pit_mmio_read',0x3c,0xa8630040),('pit_mmio_read',0x50,0xa8860070),('pit_mmio_read',0x5c,0xe8660004),('pit_mmio_read',0x60,0xf0670000),('read_word',0x94,0x30a00008),('read_word',0xdc,0x80000000),('pit_terminal_audit',4,0x80000000)]
  mutations += [('pit_mmio_composition_audit',0x24c,0x3060000d),('pit_mmio_composition_audit',0x254,0x64a40400),('pit_mmio_composition_audit',0x25c,0xd005d800)]
  for m in mutations:
   with self.assertRaises(ValueError,msg=str(m)):check(*fixture(m))
 def test_every_scoped_word_mutation_rejected(self):
  for name,(_,size,_) in PINS.items():
   for offset in range(0,size,4):
    with self.assertRaises(ValueError):check(*fixture((name,offset,0xffffffff)))
 def test_stale_missing_duplicate_ranges_rejected(self):
  with self.assertRaises(ValueError):check(*fixture(('pit_mmio_read',0x5c,0x80000000),stale=True))
  data,symbols,text=fixture()
  for bad in [symbols.replace(' T pit_mmio_read',' T wrong'),symbols+'\n'+symbols.splitlines()[0],symbols.replace('00000070 T pit_mmio_read','0000006c T pit_mmio_read')]:
   with self.assertRaises(ValueError):check(data,bad,text)
  with self.assertRaises(ValueError):check(data,symbols,text+'\n'+text.splitlines()[0])
if __name__=='__main__':unittest.main()
