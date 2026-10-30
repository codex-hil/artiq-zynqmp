# SPDX-License-Identifier: LGPL-3.0-or-later
"""Scoped new entry initializer/call inventory, not generic transitive flow proof."""
import collections,json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
from check_pmu_boundary_image import check as layout
from check_pit_word_stores import check as stores
from package_local_candidate import loads
ENTRY='pit_mmio_composition_audit'
NAMES=[ENTRY,'pit_mmio_read','pit_terminal_audit','observe','disable','read_word','write_word','barrier']
INIT={0x248:0x10980000,0x24c:0x3060000c,0x250:0x3361001c,0x254:0x64a40402,0x258:0x3063ffff,0x25c:0xd805d800,0x260:0xbe23fff4,0x264:0x30840001}
def check(data,symbols,text):
 sym={m[3]:(int(m[1],16),int(m[2],16)) for line in symbols.splitlines() if (m:=re.fullmatch(r'([0-9a-f]+) ([0-9a-f]+) [tT] (\S+)',line))}
 start,size=sym[ENTRY];rows={int(a,16):(int(w,16),op) for a,w,op in re.findall(r'^\s*([0-9a-f]+):\s+([0-9a-f]{8})\s+(\w+)',text,re.M)}
 _,_,segments=loads(data)
 for name in NAMES:
  a,n=sym[name]
  for pc in range(a,a+n,4):
   spans=[s for s in segments if s['address']<=pc and pc+4<=s['address']+s['filesz']]
   if len(spans)!=1:raise ValueError('missing instruction bytes')
   s=spans[0]
   if rows[pc][0]!=int.from_bytes(s['payload'][pc-s['address']:pc-s['address']+4],'little'):raise ValueError('stale instruction listing')
 for offset,word in INIT.items():
  if rows[start+offset][0]!=word:raise ValueError('changed 12-word volatile initializer')
 calls=[]
 for pc in range(start,start+size,4):
  word,op=rows[pc]
  if op=='brlid':
   delta=word&65535;bits=16;prior=rows.get(pc-4,(0,''))[0]
   if prior>>16==0xb000:delta|=(prior&65535)<<16;bits=32
   if delta&(1<<(bits-1)):delta-=1<<bits
   target=(pc+delta)&0xffffffff;name=next((n for n,(a,_) in sym.items() if a==target),None)
   calls.append({'pc':hex(pc),'target':hex(target),'name':name})
 expected=collections.Counter(observe=3,disable=1,read_word=1,write_word=3,barrier=2,pit_terminal_audit=1)
 if collections.Counter(c['name'] for c in calls)!=expected:raise ValueError('unexpected direct call, including possible library path')
 return {'hardware_executed':False,'deployable':False,'initializer_words':12,'initializer_critical_pins':len(INIT),'direct_calls':calls,'no_entry_memset_call':True,'word_stores':{n:stores(data,symbols,n) for n in NAMES},'layout':layout(data,symbols),'limits':'Exact initializer word pins and named direct-call inventory only. Indirect external callback/library/exception paths and full CFG/dataflow/stack/liveness remain unqualified.'}
if __name__=='__main__':
 b=Path('/home/codex-hil/.local/state/artiq-builds/pit-mmio-word-init-audit-20261030-v1')
 print(json.dumps(check((b/'audit-only.elf').read_bytes(),(b/'symbols.txt').read_text(),(b/'disassembly.txt').read_text()),indent=2))
