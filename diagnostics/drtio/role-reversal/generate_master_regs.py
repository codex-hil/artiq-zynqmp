#!/usr/bin/env python3
"""Generate exact candidate CSR definitions; LGPL-3.0-or-later."""
import argparse,hashlib,json
from pathlib import Path
REQUIRED={'kernel_target':(32,1),'kernel_now':(64,2),'kernel_o_data':(512,16),'kernel_o_status':(3,1),'profile_identity':(32,1),'profile_fine_width':(32,1),'profile_coarse_hz':(32,1),'routing_selected':(1,1),'master_rx_up':(1,1)}
def generate(path):
 raw=Path(path).read_bytes();m=json.loads(raw)
 if (m['kind'],m['identity'],m['fine_ts_width'],m['timestamp_unit_ps'],m['coarse_hz'],m['csr_base'])!=('genesys-master-candidate-not-local-rtio-abi',0x47534d31,3,1000,125000000,0xa0000000):raise ValueError('Wrong master profile/time units')
 used=set();lines=['/* LGPL-3.0-or-later; generated, do not hand-edit. */','#pragma once','#include <stdint.h>','/* Map SHA256 '+hashlib.sha256(raw).hexdigest()+' */','#define GM_IDENTITY UINT32_C(0x47534d31)']
 for name,(bits,words) in REQUIRED.items():
  r=m['registers'][name];a=r['address']
  if (r['bits'],r['words'],r['word_order'],r['word_bytes'])!=(bits,words,'big',4) or type(a) is not int or a%4 or not 0xa0000000<=a<=0xa0002000-words*4:raise ValueError('Wrong CSR shape: '+name)
  slots=set(range(a,a+4*words,4))
  if slots&used:raise ValueError('Overlapping CSR: '+name)
  used|=slots;lines.append('#define GM_'+name.upper()+' UINT32_C(0x%08x)'%a)
 return '\n'.join(lines)+'\n'
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--map',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.write_text(generate(a.map))
