"""Pinned no-master image gate for trained observer; LGPL-3.0-or-later."""
import hashlib,json
from pathlib import Path
from check_remote_rtio_build import check
SCRIPTS={'scripts/no_master_candidate.py','scripts/check_remote_rtio_build.py','scripts/program_genesys_pl.tcl','scripts/test_candidate_runtime_hw.py','scripts/run_trained_observer.py'}
def preflight(path,repo):
 m=json.loads(Path(path).read_text())
 if set(m)!={'bitstream','build_inputs','script_sha256'} or set(m['script_sha256'])!=SCRIPTS:raise ValueError('Exact no-master gate required')
 for n,h in m['script_sha256'].items():
  if hashlib.sha256((repo/n).read_bytes()).hexdigest()!=h:raise ValueError('Changed no-master helper '+n)
 for key in ('bitstream','build_inputs'):
  item=m[key]
  if hashlib.sha256(Path(item['path']).read_bytes()).hexdigest()!=item['sha256']:raise ValueError('Changed no-master artifact '+key)
 inputs=json.loads(Path(m['build_inputs']['path']).read_text())
 if inputs.get('profile')!='no-ddr-master':raise ValueError('Wrong build profile')
 bit=Path(m['bitstream']['path'])
 if bit.name!='top.bit':raise ValueError('Unexpected bitstream layout')
 check(bit.parent,inputs)
 return m

def verify_configuration(window):
 context=window['observations']['pcap_context']
 if not context['stable'] or context['status_fields']['fields']['pl_done']!=[True,True]:
  raise ValueError('No stable PL DONE after no-master load')
 return {'status':'NO_MASTER_PL_CONFIGURED_OBSERVATION_ONLY','destructive_test_allowed':False}
