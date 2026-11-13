#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Account for CDC paths under diagnostic clock-mode assumptions, no waiver."""
import argparse,importlib.util,json,hashlib
from pathlib import Path
p=Path(__file__).with_name('classify-combined-cdc.py');s=importlib.util.spec_from_file_location('cdc',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
p=argparse.ArgumentParser();p.add_argument('directory',type=Path);a=p.parse_args();d=a.directory
old,oldrows=m.parse((d/'baseline-cdc.rpt').read_text());new,newrows=m.parse((d/'steady-cdc.rpt').read_text())
def key(r):return tuple(r[n] for n in ('id','severity','source','destination','source_clock','destination_clock'))
b={key(r):r for r in oldrows};c={key(r):r for r in newrows};assert len(b)==len(oldrows) and len(c)==len(newrows)
result={'status':'DIAGNOSTIC_MODE_CDC_COMPARISON_ACCOUNTED_NOT_QUALIFIED','baseline':old,'steady':new,'baseline_rows':len(b),'steady_rows':len(c),'removed_paths':[b[k] for k in sorted(b.keys()-c.keys())],'added_paths':[c[k] for k in sorted(c.keys()-b.keys())],'same_paths':len(b.keys()&c.keys()),'limits':['Six selector010 and three primitive RXRATE000 cases are explicit steady-mode assumptions','Disappearing CDC paths are model-dependent, not fixed or waived circuitry','Equal8ns periods or common generated masters do not prove physical recovered-clock phase or deterministic latency','No saved DCP/default/hardware changes or broad exceptions'],'next':'Review changed CDC endpoints and clock-interaction classifications against source protocol before considering any runtime constraints'}
result['report_sha256']={name:hashlib.sha256((d/name).read_bytes()).hexdigest() for name in ('baseline-cdc.rpt','steady-cdc.rpt','baseline-interaction.rpt','steady-interaction.rpt')}
(d/'comparison.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ('baseline','steady','baseline_rows','steady_rows','same_paths')}))
