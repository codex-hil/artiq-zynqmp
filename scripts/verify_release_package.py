#!/usr/bin/env python3
"""Offline candidate-package consistency check; LGPL-3.0-or-later.

Validates local input/output hashes and binds reused PL/FSBL/PMU to a pinned
baseline profile. This is not a signature, boot proof or hardware qualification.
"""
import argparse,hashlib,json,re
from pathlib import Path
from run_qualified_drtio import REPO,validate


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(package,pinned):
    manifest=json.loads((package/'artifacts.json').read_text())
    if manifest.get('kind')!='packaged-artifacts-not-boot-proof':
        raise ValueError('Unexpected package manifest kind')
    artifacts=manifest['artifacts']
    if set(artifacts)!={'fsbl','pmufw','bitstream','application','worker_boot','boot.bin'}:
        raise ValueError('Expected complete two-CPU package')
    verified={}
    for name,entry in artifacts.items():
        expected=entry['sha256']
        if not re.fullmatch('[0-9a-f]{64}',expected):raise ValueError('Invalid digest')
        path=package/'boot.bin' if name=='boot.bin' else Path(entry['path'])
        actual=digest(path)
        if actual!=expected:raise ValueError('Hash mismatch: '+name)
        if name in ('fsbl','pmufw','bitstream') and expected!=pinned.get(name):
            raise ValueError('Reused baseline input is not pinned: '+name)
        verified[name]=dict(path=str(path),sha256=actual)
    return dict(status='CONSISTENCY_PASS_NOT_BOOT_PROOF',hardware_executed=False,
                artifacts=verified,scope='Self-consistency and pinned baseline roles only; no BIF/ELF compatibility or cold-boot qualification')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--package',type=Path,required=True)
    p.add_argument('--baseline-profile',type=Path,required=True)
    p.add_argument('--artifact-root',type=Path,default=Path('/srv/codex-hil-data/artiq-zynqmp'))
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    if a.output.exists():raise ValueError('Refusing to overwrite report')
    variables=dict(repo=str(REPO),artifacts=str(a.artifact_root.resolve()),home=str(Path.home()),output=str(a.output.parent.resolve()))
    data,verified=validate(json.loads(a.baseline_profile.read_text()),variables)
    pins={str(Path(entry['path']).resolve()):entry['sha256'] for entry in verified}
    ps=Path(data['observer']['ps_export'])
    roles=dict(bitstream=data['observer']['restore_bitstream'],fsbl=str(ps/'app/build/zynqmp_fsbl.elf'),pmufw=str(ps/'pmu-app/build/zynqmp_pmufw.elf'))
    report=verify(a.package.resolve(),{role:pins[str(Path(path).resolve())] for role,path in roles.items()})
    report.update(baseline_profile_sha256=digest(a.baseline_profile),manifest_sha256=digest(a.package/'artifacts.json'))
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open('x') as f:f.write(json.dumps(report,indent=2)+'\n')
    print(report['status'])

if __name__=='__main__':main()
