#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Lossless CDC row inventory; name-based triage never grants CDC waivers."""
import argparse,collections,hashlib,json,re
from pathlib import Path

def parse(text):
 summary={i:(s,int(n)) for i,s,n in re.findall(r'^(CDC-\d+)\s+(Critical|Warning|Info)\s+(\d+)\s+.+$',text,re.M)}
 rows=[];source=destination=None
 pattern=re.compile(r'^\s*(\d+)\s+(CDC-\d+)\s+(Critical|Warning|Info)\s+(.+?)\s{2,}(\d+)\s+(\S+)\s+(\S+)\s+(\S+)\s*$')
 for line in text.splitlines():
  if line.startswith('Source Clock: '):source=line[len('Source Clock: '):]
  if line.startswith('Destination Clock: '):destination=line[len('Destination Clock: '):]
  m=pattern.match(line)
  if m:
   assert source and destination
   row,i,severity,description,depth,exception,src,dst=m.groups()
   rows.append(dict(row=int(row),id=i,severity=severity,description=description.strip(),depth=int(depth),exception=exception,source=src,destination=dst,source_clock=source,destination_clock=destination))
 counts=collections.Counter(r['id'] for r in rows)
 assert summary and counts=={i:n for i,(s,n) in summary.items()},(counts,summary)
 assert all(r['severity']==summary[r['id']][0] for r in rows)
 return summary,rows

def classify(row):
 src,dst=row['source'],row['destination']
 if 'drtio_gth/' in src or 'drtio_gth/' in dst or 'gtwizard_' in src or 'gtwizard_' in dst:return 'VENDOR_GT_NAME_REVIEW_REQUIRED'
 if row['id'] in ('CDC-10','CDC-11') and ('FDPE' in dst or 'ingress_outputs_reset_reg' in src):return 'RESET_OR_REGISTERED_RESET_NAME_REVIEW_REQUIRED'
 if 'gray' in src.lower() or 'gray' in dst.lower():return 'GRAY_NAME_PROTOCOL_AND_CONSTRAINT_REVIEW_REQUIRED'
 return 'OTHER_UNCLASSIFIED_REVIEW_REQUIRED'

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('report',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
 raw=a.report.read_text();summary,rows=parse(raw)
 for r in rows:r['triage']=classify(r)
 # Refuse report truncation even if retained rows remain syntactically valid.
 try:parse(raw[:raw.rfind('\n',0,raw.rfind('CDC-'))])
 except AssertionError:pass
 else:raise AssertionError('Truncated report accepted')
 selected=[r for r in rows if r['id'] in ('CDC-10','CDC-11')]
 a.output.mkdir(parents=True,exist_ok=True)
 (a.output/'rows.json').write_text(json.dumps(rows,indent=2)+'\n')
 (a.output/'reset-and-fanout.json').write_text(json.dumps(selected,indent=2)+'\n')
 result={'status':'COMPLETE_ROW_ACCOUNTING_NOT_CDC_SIGNOFF','raw_sha256':hashlib.sha256(a.report.read_bytes()).hexdigest(),'rows':len(rows),'summary':summary,'triage':dict(collections.Counter(r['triage'] for r in rows)),'reset_and_fanout_count':len(selected),'truncation_mutant':'REFUSED','limits':['Classification uses names, not synthesized fan-in proof','All severities retained; vendor and Gray names are not waivers','Separate isolated reset result does not qualify full reset fanout'],'next':'Read-only full synthesized DCP fan-in and reset endpoint mapping for 12 CDC10 and 4 CDC11 paths'}
 (a.output/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
