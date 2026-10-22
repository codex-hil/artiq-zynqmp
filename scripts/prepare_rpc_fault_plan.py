#!/usr/bin/env python3
"""Prepare bounded RPC fault cases; offline only; LGPL-3.0-or-later."""
import argparse,hashlib,json,struct
from pathlib import Path
from test_candidate_runtime_hw import preflight


def cases():
    # Reply bodies start after upstream Request.RPCReply (wire type7).
    return [dict(name='zero_descriptor_length',body_hex='00000000',half_close=False,expected='transport_abort_cancel_worker'),
            dict(name='unsupported_return_tag',body_hex=(struct.pack('<I',1)+b'?').hex(),half_close=False,expected='transport_abort_cancel_worker'),
            dict(name='partial_float_eof',body_hex=(struct.pack('<I',1)+b'f'+bytes(3)).hex(),half_close=True,expected='peer_eof_cancel_worker')]


def prepare(manifest,output):
    if output.exists():raise ValueError('Use a fresh plan output')
    value=json.loads(manifest.read_text());preflight(value)
    steps=[]
    for case in cases():
        steps.append(dict(case=case,sequence=['acquire_shared_genesys_lease','verify_all_candidate_restore_hashes','load_candidate_and_verify_identity','run_one_kernel_until_synchronous_float_rpc','inject_once','require_connection_termination_and_management_alive','restore_old_baseline_even_on_failure','validate_restored_physical_debug_and_ethernet','release_lease'],reuse_after_fault=False))
    report=dict(status='OFFLINE_FAULT_PLAN_NOT_EXECUTED',hardware_executed=False,
        manifest=str(manifest.resolve()),manifest_sha256=hashlib.sha256(manifest.read_bytes()).hexdigest(),
        cable=value['cable'],lease=value['lease'],steps=steps,
        gate='No hardware executor in this tool. Each case needs a separate outer restoration window; do not reuse faulted worker.',
        limits='Socket close/management liveness alone do not prove CPU1 cancellation progress. Record that separately or leave NOT_PROVEN.')
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open('x') as f:f.write(json.dumps(report,indent=2)+'\n')
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--manifest',required=True,type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
    print(json.dumps(prepare(a.manifest,a.output),indent=2))

if __name__=='__main__':main()
