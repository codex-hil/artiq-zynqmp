#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Validate requested diagnostic mode receipts; not physical clock measurements."""
import argparse,itertools,json,hashlib
from pathlib import Path
def parse(text):
 modes={}
 for line in text.splitlines():
  f=line.split('\t')
  if f[0]=='MODE':assert f[1] not in modes;modes[f[1]]={'cases':{},'clocks':{},'buffers':{}}
  elif f[0]=='CASE':assert f[2] not in modes[f[1]]['cases'];modes[f[1]]['cases'][f[2]]=int(f[3])
  elif f[0]=='CLOCK':modes[f[1]]['clocks'][f[2]]=float(f[3])
  elif f[0]=='BUFFER':modes[f[1]]['buffers'][f[2]]=f[3] if len(f)>3 else ''
 expected={f'tx{tx}_rxrate{rate}':(tx,rate) for tx,rate in itertools.product(('000','101','010'),('001','000'))}
 assert set(modes)==set(expected)
 for label,(tx,rate) in expected.items():
  wanted={f'{kind}[{bit}]':(int(word,2)>>bit)&1 for kind,word in (('TXOUTCLKSEL',tx),('RXOUTCLKSEL','010'),('RXRATE',rate)) for bit in range(3)}
  assert modes[label]['cases']==wanted
 return modes
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('directory',type=Path);a=p.parse_args();raw=(a.directory/'matrix.tsv').read_text();modes=parse(raw)
 lines=raw.splitlines();index=next(i for i,l in enumerate(lines) if l.startswith('CASE\t'))
 try:parse('\n'.join(lines[:index]+lines[index+1:]))
 except AssertionError:pass
 else:raise AssertionError('Missing case mutation accepted')
 summary={name:{'tx_ns':r['clocks'].get('txoutclk_out[0]'),'rx_ns':r['clocks'].get('rxoutclk_out[0]')} for name,r in modes.items()}
 result={'status':'SIX_DIAGNOSTIC_MODES_54_REQUESTED_PIN_VALUES_ACCOUNTED','summary':summary,'modes':modes,'missing_case_mutant':'REFUSED','receipt_sha256':hashlib.sha256((a.directory/'matrix.tsv').read_bytes()).hexdigest(),'limits':['Requested set_case_analysis values logged, not independent hardware/pin case readback','Absent derived clock is not proof a physical clock stops','Mode cross-product not a proof of reachable mode combinations or fastest active Gray source','No numeric constraints/period overrides/CDC waivers or saved DCP'],'next':'Correlate selector/rate changes with PMA reset-done and userclk clear timeline before treating any period as active-producer bound'}
 (a.directory/'comparison.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(summary))
