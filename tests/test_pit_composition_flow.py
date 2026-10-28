"""Consistent synthetic ELF/disassembly mutations of real archived bodies. LGPL-3.0-or-later."""
import re
import struct
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from check_pit_composition_flow import check,ENTRY,FORWARDERS
ARCHIVE=ROOT/'evidence/pit-forwarded-status-target-offline-2026-10-27'


def fixture(mutation=None,stale=False,shape="forwarded-v1"):
    names=[ENTRY,*FORWARDERS,'pit_terminal_audit']
    archive=ARCHIVE if shape=='forwarded-v1' else ROOT/'evidence/pit-ro-target-context-offline-2026-10-28'
    texts={name:(archive/(name+'.dis')).read_text() for name in names}
    original_rows={}
    for text in texts.values():
        for a,w in re.findall(r'^([0-9a-f]+):\s+([0-9a-f]{8})',text,re.M):original_rows[int(a,16)]=int(w,16)
    changed_pc=None;changed_word=None
    if mutation:
        name,op,new_op,transform=mutation
        if op.startswith('@'):
            first=int(re.search(r'^([0-9a-f]+):',texts[name],re.M)[1],16)
            pattern=r'^('+format(first+int(op[1:],16),'08x')+r'):\s+([0-9a-f]{8})\s+.*$'
        else:
            pattern=r'^([0-9a-f]+):\s+([0-9a-f]{8})\s+'+re.escape(op)+r'\b.*$'
        match=re.search(pattern,texts[name],re.M)
        assert match
        changed_pc=int(match[1],16);changed_word=transform(int(match[2],16))
        if not stale:
            texts[name]=texts[name][:match.start()]+f'{changed_pc:08x}:\t{changed_word:08x} \t{new_op} synthetic'+texts[name][match.end():]
    rows=dict(original_rows)
    if mutation:rows[changed_pc]=changed_word
    base=min(rows);payload=bytearray(max(rows)-base+4)
    for pc,word in rows.items():struct.pack_into('<I',payload,pc-base,word)
    symbols=[]
    for name,text in texts.items():
        addresses=[int(a,16) for a in re.findall(r'^([0-9a-f]+):',text,re.M)]
        symbols.append(f'{min(addresses):08x} {max(addresses)-min(addresses)+4:08x} T {name}')
    symbols.append(('ffdd265c' if shape=='forwarded-v1' else 'ffdd2760')+' 00000114 T memset')
    ident=b'\x7fELF\x01\x01\x01'+bytes(9)
    header=struct.pack('<HHIIIIIHHHHHH',2,189,1,0xffdc0050,52,0,0,52,32,1,0,0,0)
    ph=struct.pack('<8I',1,84,base,base,len(payload),len(payload),7,4)
    return ident+header+ph+payload,'\n'.join(symbols),'\n'.join(texts.values())


class Tests(unittest.TestCase):
    def test_archived_scoped_inventory(self):
        result=check(*fixture())
        self.assertEqual(result['functions'][ENTRY]['direct_calls'],12)
        self.assertEqual(result['functions'][ENTRY]['internal_branches'],97)
        self.assertFalse(result['deployable'])

    def test_ro_context_v2_address_budget_and_state_mutations(self):
        result=check(*fixture(shape='ro-context-v2'),shape='ro-context-v2')
        self.assertEqual(result['functions']['read_word']['critical_word_pins'],30)
        mutations=[
            ('read_word','@b8','addik',lambda w:(w&0xffff0000)|0x40), # WO preload alias
            ('read_word','@b4','imm',lambda w:0xb000ffd5), # Wrong register bank
            ('read_word','@94','addik',lambda w:0x30a00008), # Ninth read admitted
            ('read_word','@ac','andi',lambda w:0xa4a40001), # Wrong timer sequence
            ('read_word','@7c','or',lambda w:0x80000000), # Busy guard removed
            ('read_word','@84','or',lambda w:0x80000000), # Failed-state guard removed
            ('read_word','@dc','or',lambda w:0x80000000), # Count not consumed before call
            ('read_word','@e8','or',lambda w:0x80000000), # Raw error ignored
            (ENTRY,'@34','or',lambda w:0x80000000), # Audit entry accepts null adapter
        ]
        for mutation in mutations:
            with self.assertRaises(ValueError):
                check(*fixture(mutation,shape='ro-context-v2'),shape='ro-context-v2')
        for fixture_shape,checker_shape in [('forwarded-v1','ro-context-v2'),('ro-context-v2','forwarded-v1')]:
            with self.assertRaises(ValueError):check(*fixture(shape=fixture_shape),shape=checker_shape)

    def test_consistent_control_mutations_rejected(self):
        mutations=[
            ('pit_terminal_audit','mbar','or',lambda w:0x80000000),
            (ENTRY,'brlid','brlid',lambda w:(w&0xffff0000)|((w+4)&65535)),
            (ENTRY,'brald','brald',lambda w:0x99fcd800),
            ('observe','brald','brald',lambda w:0x99fc2000),
            (ENTRY,'addik','rtsd',lambda w:0xb60f0008),
            ('read_word','rtsd','rtid',lambda w:0xb62f0008),
            (ENTRY,'beqid','beqid',lambda w:(w&0xffff0000)|0x7ffc),
            (ENTRY,'swi','sbi',lambda w:(w&0x03ffffff)|0xf0000000),
        ]
        for mutation in mutations:
            with self.assertRaises(ValueError):check(*fixture(mutation))
        with self.assertRaises(ValueError):check(*fixture(mutations[0],stale=True))
        data,symbols,text=fixture()
        with self.assertRaises(ValueError):check(data,symbols.replace(' T observe',' T missing_observe'),text)


if __name__=='__main__':unittest.main()
