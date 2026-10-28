# SPDX-License-Identifier: LGPL-3.0-or-later
"""Offline checkpoint hashes and archived replay only; no hardware executor."""
import hashlib,importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
def verify():
 m=json.loads((HERE/'manifest.json').read_text())
 for name,digest in m['sha256'].items():
  if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=digest:raise ValueError('changed checkpoint input: '+name)
 for name in m['historical_input_manifests']:
  for path,digest in json.loads((ROOT/name).read_text()).items():
   if hashlib.sha256((ROOT/path).read_bytes()).hexdigest()!=digest:raise ValueError('changed historical source: '+path)
 p=ROOT/'evidence/pit-session-c-replay-offline-2026-10-28/replay.py'
 spec=importlib.util.spec_from_file_location('checkpoint_replay',p);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
 report=mod.replay();old=json.loads((ROOT/'evidence/pit-session-c-replay-offline-2026-10-28/report.json').read_text())
 if report!=old:raise ValueError('archived replay differs from recorded result')
 assert report['cases']==11 and len(report['correlated_traces'])==33 and len(report['negative_controls'])==44
 return {'status':'OFFLINE_OBSERVER_SESSION_STAGE_COMPLETE','hardware_executed':False,'deployable':False,'destructive_test_allowed':False,'pinned_files':len(m['sha256']),'historical_source_manifests_verified':len(m['historical_input_manifests']),'archived_replay_identical':True,'pit_tests_last_pass':72,'host_suite_rerun':False,'remaining_physical_blockers':m['remaining_physical_blockers'],'next_physical_step_admitted':False}
if __name__=='__main__':print(json.dumps(verify(),indent=2))
