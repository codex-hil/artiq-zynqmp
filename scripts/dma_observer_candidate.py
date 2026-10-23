"""Pinned optional observer candidate gate; LGPL-3.0-or-later."""
import hashlib,json
from pathlib import Path
from check_dma_observer_snapshot import check_map,parse
SCRIPTS={
 'scripts/dma_observer_candidate.py','scripts/check_dma_observer_snapshot.py',
 'scripts/probe_dma_observer.tcl','scripts/test_candidate_runtime_hw.py',
 'scripts/check_remote_rtio_build.py','scripts/check_hw_storage.py',
 'scripts/load_rtio_runtime.py','scripts/reset_genesys_ps.tcl',
 'scripts/run_boot_firmware.tcl','scripts/prepare_local_rtio.tcl',
 'scripts/run_kernel_worker.tcl','scripts/run_a53_runtime.tcl',
 'scripts/program_genesys_pl.tcl','scripts/test_rtio_debug_hw.py',
 'scripts/test_ethernet_hw.py','scripts/run_dma_observer_active.py',
 'scripts/check_dma_observer_active.py','scripts/probe_dma_observer_active.tcl',
 'scripts/inject_rpc_fault.py','examples/genesys_dma_observer_load.py'}


def preflight(info,files,repo):
    if set(info)!={'build_inputs','script_sha256'}:raise ValueError('Exact observer gate required')
    if set(info['script_sha256'])!=SCRIPTS:raise ValueError('Missing observer execution pins')
    for n,h in info['script_sha256'].items():
        if hashlib.sha256((repo/n).read_bytes()).hexdigest()!=h:raise ValueError('Changed observer helper '+n)
    item=info['build_inputs'];p=Path(item['path'])
    if hashlib.sha256(p.read_bytes()).hexdigest()!=item['sha256']:raise ValueError('Changed observer build inputs')
    build=Path(files['candidate_pl']['path']).parent
    if Path(files['candidate_csr']['path']).resolve()!=(build/'csr-map.json').resolve():raise ValueError('Observer map not bound to build')
    check_map(build/'csr-map.json')
    generated=json.loads((build/'generation.json').read_text())
    if generated.get('dma_observer') is not True:raise ValueError('Not observer generation')
    # The strict build checker, called by the parent, binds generation.json inputs
    # to actual files/reports, including the CSR map. Never trust a PASS receipt alone.
    return p


def verify_snapshot(text):
    result=parse(text)
    if not result['stable'] or result['error_observed'] or not result['zero_count_observed']:
        raise ValueError('Observer not stable/zero/error-free after bounded workload')
    return result
