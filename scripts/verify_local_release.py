#!/usr/bin/env python3
"""Offline local release-chain verification; LGPL-3.0-or-later."""
import argparse,json
from pathlib import Path
from check_remote_rtio_build import check,sha
from compare_bitstreams import compare
from package_local_candidate import verify_proof,match_worker,loads
from verify_boot_payloads import partitions,match


def bind_package(package,manifest,proof,files):
    release=json.loads((package/'release.json').read_text())
    if release['manifest_sha256']!=sha(manifest) or release['extended_jtag_proof_sha256']!=sha(proof):
        raise ValueError('Package proof binding mismatch')
    artifacts=json.loads((package/'artifacts.json').read_text())['artifacts']
    for role,candidate in [('fsbl','candidate_fsbl'),('pmufw','candidate_pmu'),
                           ('application','candidate_cpu0'),('bitstream','candidate_pl')]:
        item=artifacts[role]
        if item['sha256']!=files[candidate]['sha256'] or sha(Path(item['path']))!=item['sha256']:
            raise ValueError('Package role mismatch: '+role)
    bridge=Path(artifacts['worker_boot']['path'])
    if sha(bridge)!=release['sd_bridge_sha256'] or sha(bridge)!=artifacts['worker_boot']['sha256']:
        raise ValueError('Bridge hash mismatch')
    embedded=match_worker(Path(files['candidate_worker']['path']).read_bytes(),bridge.read_bytes())
    if embedded!=release['worker_embedding']:raise ValueError('Worker embedding report mismatch')
    image=(package/'BOOT.BIN').read_bytes()
    if sha(package/'BOOT.BIN')!=release['boot_bin_sha256'] or release['boot_bin_sha256']!=artifacts['boot.bin']['sha256']:
        raise ValueError('Boot image hash mismatch')
    parts=partitions(image);payloads=[]
    for role,cpu in [('worker_boot',2),('application',1)]:
        machine,entry,segments=loads(Path(artifacts[role]['path']).read_bytes())
        if machine!=183:raise ValueError('Unexpected CPU ELF architecture')
        payloads+=match(parts,segments,cpu,role)
    return dict(boot_bin_sha256=release['boot_bin_sha256'],worker_embedding=embedded,
                partition_headers_checked=len(parts),cpu_payloads=payloads)


def verify(config):
    manifest=Path(config['candidate_manifest']);proof=Path(config['hardware_proof'])
    files=verify_proof(manifest,proof)
    build=Path(config['source_build']);inputs=Path(config['build_inputs'])
    fpga=check(build,json.loads(inputs.read_text()))
    equivalence=compare(Path(files['candidate_pl']['path']).read_bytes(),(build/'top.bit').read_bytes())
    if equivalence['status']!='CONFIGURATION_BYTES_IDENTICAL':raise ValueError('Source build differs from qualified configuration')
    package=bind_package(Path(config['package']),manifest,proof,files)
    return dict(status='LOCAL_RELEASE_CHAIN_PASS_COLD_BOOT_NOT_RUN',hardware_executed=False,cold_boot='NOT_RUN',
                manifest_sha256=sha(manifest),hardware_proof_sha256=sha(proof),build_inputs_sha256=sha(inputs),
                fpga=fpga,configuration_equivalence=equivalence,package=package,
                limits='Offline consistency of selected artifacts and recorded hardware proof; not signed provenance, fresh hardware execution, complete source bootstrap, FSBL/PMU/PL serialized payload verification or cold boot.')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',required=True,type=Path);parser.add_argument('--output',required=True,type=Path)
    a=parser.parse_args()
    if a.output.exists():raise ValueError('Use a fresh report path')
    config=json.loads(a.config.read_text());report=verify(config);report['config_sha256']=sha(a.config)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open('x') as f:f.write(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
