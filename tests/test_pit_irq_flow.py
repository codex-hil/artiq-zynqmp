# SPDX-License-Identifier: LGPL-3.0-or-later
import re,struct,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from check_pit_irq_flow import check,PINS,STORAGE_PINS
MUTANTS=[('pit_irq_composition_audit', 200, 811647508), ('pit_irq_composition_audit', 212, 811647556), ('pit_irq_composition_audit', 216, 2147483648), ('pit_irq_composition_audit', 220, 4167368820), ('pit_irq_msr_audit', 32, 2147483648), ('pit_irq_msr_audit', 36, 3496345600), ('pit_irq_disable_audit', 20, 2147483648), ('microblaze_disable_interrupts', 4, 3898641304), ('microblaze_disable_interrupts', 8, 2147483648), ('microblaze_disable_interrupts', 12, 2484142336), ('microblaze_disable_interrupts', 32, 2758016767), ('microblaze_disable_interrupts', 36, 2147483648)]
def fixture(mutation=None,stale=False):
 archive=ROOT/'evidence/pit-irq-binding-offline-2026-10-31'
 texts={n:(archive/(n+'.dis')).read_text() for n in PINS}
 rows={int(a,16):int(w,16) for text in texts.values() for a,w in re.findall(r'^([0-9a-f]+):\s+([0-9a-f]{8})',text,re.M)}
 if mutation:
  n,offset,word=mutation;pc=PINS[n][0]+offset;assert pc in rows and rows[pc]!=word;rows[pc]=word
  if not stale:texts[n]=re.sub(r'^'+format(pc,'08x')+r':\s+[0-9a-f]{8}\s+.*$',f'{pc:08x}:\t{word:08x}\tor synthetic',texts[n],flags=re.M)
 base=0xffdc0000;payload=bytearray(max(rows)-base+4)
 for pc,word in rows.items():struct.pack_into('<I',payload,pc-base,word)
 ident=b'\x7fELF\x01\x01\x01'+bytes(9);header=struct.pack('<HHIIIIIHHHHHH',2,189,1,0xffdc0050,52,0,0,52,32,3,0,0,0)
 ph=b''.join(struct.pack('<8I',1,148,a,a,fs,ms,flags,4) for a,fs,ms,flags in [(base,len(payload),len(payload),7),(0xffdd8000,0,0x64b0,6),(0xffddf6e0,0,0x400,6)])
 symbols=[f'{a:08x} {size:08x} T {n}' for n,(a,size,_) in PINS.items()]
 symbols += [f'{a:08x} {size:08x} {kind} {n}' for n,(a,size,kind) in STORAGE_PINS.items()]
 symbols += ['ffdd8ce0 B __bss_start','ffdd8e00 00000020 b artiq_pmu_boundary','ffddcb90 B __bss_end','ffddd4ac B _stack_end','ffdde4b0 B _stack']
 return ident+header+ph+payload,'\n'.join(symbols),'\n'.join(texts.values())
class Tests(unittest.TestCase):
 def test_reviewed_code_and_storage(self):
  x=check(*fixture());self.assertEqual(len(x['functions']),20);self.assertFalse(x['deployable']);self.assertFalse(x['mailbox']['pmu_ram_access_allowed'])
 def test_twelve_irq_binding_and_helper_mutants(self):
  for m in MUTANTS:
   with self.assertRaises(ValueError,msg=str(m)):check(*fixture(m))
 def test_each_scoped_word_mutation_rejected(self):
  for n,(_,size,_) in PINS.items():
   for offset in range(0,size,4):
    with self.assertRaises(ValueError):check(*fixture((n,offset,0xffffffff)))
 def test_storage_pins_and_stale_listing(self):
  data,symbols,text=fixture()
  for bad in [symbols.replace('ffddcab8 00000020 b sample_slot','ffddca98 00000020 b sample_slot'),symbols.replace('00000090 B pit_mailbox_audit','0000008c B pit_mailbox_audit'),symbols+'\nffddcab8 00000020 b sample_slot']:
   with self.assertRaises(ValueError):check(data,bad,text)
  with self.assertRaises(ValueError):check(*fixture(MUTANTS[0],stale=True))
if __name__=='__main__':unittest.main()
