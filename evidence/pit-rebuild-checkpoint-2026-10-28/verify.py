# SPDX-License-Identifier: LGPL-3.0-or-later
"""Read-only checkpoint verification, no hardware or build execution."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
def main():
 m=json.loads((HERE/'matrix.json').read_text())
 for row in m['rows']:
  for item in row['evidence']:
   p=ROOT/item['path']
   if hashlib.sha256(p.read_bytes()).hexdigest()!=item['sha256']:raise ValueError('changed checkpoint evidence: '+item['path'])
 p=ROOT/'evidence/pit-full-object-relink-offline-2026-10-28/report.json';x=json.loads(p.read_text())
 assert x['inputs_stable_during_link'] and not x['undefined_symbols'] and not x['load_segments_equal']
 assert len(x['segments'])==3 and all(s['metadata_equal'] for s in x['segments'])
 assert sum(len(s['differences']) for s in x['segments'])==6
 c=json.loads((ROOT/'evidence/pit-full-object-relink-offline-2026-10-28/accounting.json').read_text())
 assert c['changed_bytes']==6 and len(c['negative_controls'])==4 and all(q['rejected'] for q in c['negative_controls'])
 snap=Path('/home/codex-hil/.local/state/artiq-builds/pit-ro-frozen-audit-20261028-v1/relocated/snapshot-b')
 anchor='dad1b193758a9682a1292e1485e512e73d5f19af5991a3adbab0d5b4f69e4578'
 assert hashlib.sha256((snap/'inventory.json').read_bytes()).hexdigest()==anchor
 z=subprocess.run(['/srv/codex-hil-data/artiq-zynqmp/venv/bin/python','-I','-B',str(snap/'replay.py')],cwd='/tmp',capture_output=True,text=True,check=True)
 frozen=json.loads(z.stdout);assert frozen['deployable'] is False
 return {'status':'CHECKPOINT_EVIDENCE_AND_FROZEN_REPLAY_PASS','hardware_executed':False,'deployable':False,'evidence_rows_verified':len(m['rows']),'six_load_differences_accounted':True,'frozen_inventory_anchor_verified':True,'frozen_replay_pass':True,'host_suite_rerun':False,'limits':'Checks recorded evidence consistency and frozen audit only, not physical qualification or full trusted build provenance.'}
if __name__=='__main__':print(json.dumps(main(),indent=2))
