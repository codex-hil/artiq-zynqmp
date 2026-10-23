#!/usr/bin/env python3
"""Exact OCM model image and report gate, no DDR authorization; LGPL-3.0-or-later."""
import hashlib,json,re
from pathlib import Path
from check_ocm_image import check
SCRIPTS={'scripts/check_ddr_ocm_model.py','scripts/check_ocm_image.py','scripts/package_local_candidate.py','scripts/load_ddr_ocm_model.tcl','scripts/load_el3_exception_observer.tcl','scripts/collect_fsbl_entry.tcl'}
SYMBOLS={'__vectors':0xfffc8000,'_start':0xfffc8800,'model_done':0xfffc888c,'model_fault_done':0xfffc88b4,'model_report':0xfffc8cf0,'model_result':0xfffc8d20,'__stack0_end':0xfffe4000}
def preflight(path,repo):
 m=json.loads(Path(path).read_text())
 if set(m)!={'elf','symbols','script_sha256'} or set(m['script_sha256'])!=SCRIPTS:raise ValueError('Exact model gate required')
 for n,h in m['script_sha256'].items():
  if hashlib.sha256((repo/n).read_bytes()).hexdigest()!=h:raise ValueError('Changed model helper '+n)
 for n in ('elf','symbols'):
  item=m[n]
  if hashlib.sha256(Path(item['path']).read_bytes()).hexdigest()!=item['sha256']:raise ValueError('Changed model '+n)
 text=Path(m['symbols']['path']).read_text();check(Path(m['elf']['path']).read_bytes(),text)
 symbols={n:int(a,16) for a,n in re.findall(r'^([0-9a-fA-F]+)\s+\w\s+(\S+)$',text,re.M)}
 if any(symbols.get(n)!=v for n,v in SYMBOLS.items()):raise ValueError('Changed fixed model layout')
 return m

def parse(text):
 lines=text.splitlines()
 if lines.count('DDR_MODEL_BEGIN')!=1 or lines.count('DDR_MODEL_END')!=1:raise ValueError('Incomplete/duplicate model frame')
 start,end=lines.index('DDR_MODEL_BEGIN'),lines.index('DDR_MODEL_END')
 rows=lines[start+1:end]
 if len(rows)!=23 or any(line.startswith('DDR_MODEL') for line in lines[:start]+lines[end+1:]):raise ValueError('Unexpected frame extent')
 if rows[0]!='DDR_MODEL_PC '+str(SYMBOLS['model_done']):raise ValueError('Model not at success terminal')
 names=['x0','x14','x15','x16','x17','x18','x19','x20','x21'];regs={}
 for n,line in zip(names,rows[1:10]):
  match=re.fullmatch(r'DDR_MODEL_REG '+n+r' (\d+)',line)
  if not match:raise ValueError('Malformed model registers')
  regs[n]=int(match[1])
 if regs['x0']!=0 or regs['x15']!=0x33:raise ValueError('Model failed/faulted')
 words=[]
 for i,line in enumerate(rows[10:22]):
  match=re.fullmatch(r'DDR_MODEL_REPORT '+str(i)+r' 0x([0-9a-fA-F]{8})',line)
  if not match:raise ValueError('Malformed model report')
  words.append(int(match[1],16))
 # Header, nine registers, twelve words, one result =23 payload rows.
 if rows[22]!='DDR_MODEL_RESULT 0x00000000':raise ValueError('Model result failed')
 if (words[0]|words[1]<<32,words[2]|words[3]<<32)!=(16,16) or words[10:]!=[3,0]:raise ValueError('Model report counts/phase/error mismatch')
 address=words[4]|words[5]<<32
 expected=words[6]|words[7]<<32
 if address!=0x87ffffff8 or expected!=((~(address^0xa53dd4c0dec0ffee))&0xffffffffffffffff) or words[6:8]!=words[8:10]:raise ValueError('Model final data mismatch')
 return dict(status='A53_OCM_MODEL_REPORT_PASS_NOT_DDR',hardware_executed=True,writes=16,reads=16,phase=3,destructive_test_allowed=False)
