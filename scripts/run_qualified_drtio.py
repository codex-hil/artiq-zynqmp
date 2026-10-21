#!/usr/bin/env python3
"""Review/run one pinned laboratory DRTIO session; LGPL-3.0-or-later.

File validation is offline. Hardware execution always delegates to the existing
all-board lock/identity/restoration wrapper. Default only prepares a review.
"""
import argparse,hashlib,json,re,subprocess
from pathlib import Path

REPO=Path(__file__).resolve().parents[1]


def render(value,variables):
    if isinstance(value,str):return value.format_map(variables)
    if isinstance(value,list):return [render(v,variables) for v in value]
    if isinstance(value,dict):return {k:render(v,variables) for k,v in value.items()}
    return value


def validate(profile,variables):
    if profile.get('schema') not in (1,2):raise ValueError('Unsupported qualification profile')
    data=render(profile,variables)
    expected_wrapper=str(REPO/'scripts/test_kasli03_netboot_hw.py')
    if len(data.get('argv',[]))<2 or data['argv'][1]!=expected_wrapper:
        raise ValueError('Only the existing guarded Kasli/Genesys wrapper is supported')
    if not data.get('artifacts'):raise ValueError('No pinned artifacts')
    verified=[]
    for entry in data['artifacts']:
        digest=entry['sha256']
        if not re.fullmatch('[0-9a-f]{64}',digest):raise ValueError('Invalid artifact digest')
        path=Path(entry['path'])
        if not path.is_file():raise ValueError('Missing artifact: '+str(path))
        actual=hashlib.sha256(path.read_bytes()).hexdigest()
        if actual!=digest:raise ValueError('Artifact hash mismatch: '+str(path))
        verified.append(dict(path=str(path),sha256=actual))
    pinned={str(Path(v['path']).resolve()):v['sha256'] for v in verified}
    def option(name):
        try:return data['argv'][data['argv'].index(name)+1]
        except (ValueError,IndexError):raise ValueError('Missing wrapper option: '+name)
    runtime=option('--download-runtime')
    kasli_bit=str(Path(option('--build'))/'generated/genesys_drtio_master_v11/gateware/top.bit')
    required=[runtime,kasli_bit,option('--qualification'),*data.get('pass_proofs',[])]
    required += [data['observer'][k] for k in ('bitstream','csr_map','firmware','restore_bitstream','cpu0')]
    if data['schema']==1:
        required += [str(Path(data['observer']['dma_cursor_overlay'])/'results.json')]
    else:
        required += [option(k) for k in ('--clock-plan','--clock-baseline','--clock-validation')]
    if any(str(Path(v).resolve()) not in pinned for v in required):
        raise ValueError('Wrapper/observer references an unpinned artifact')
    if pinned[str(Path(runtime).resolve())]!=option('--runtime-sha256') or pinned[str(Path(kasli_bit).resolve())]!=option('--sha256'):
        raise ValueError('Wrapper digest differs from pinned artifact')
    for name in data.get('pass_proofs',[]):
        proof=json.loads(Path(name).read_text())
        if proof.get('status')!='PASS' or proof.get('restoration')!='PASS':
            raise ValueError('Qualification/restoration is not PASS: '+name)
    observer=data['observer']
    if data['schema']==1:
        if not (observer.get('native_ddma_catch') and observer.get('native_ddma_cursor')):
            raise ValueError('This profile must retain the qualified catch/cursor test')
    else:
        if data.get('qualification')!='kasli04-basic-native-dma' or option('--board')!='KASLI04':
            raise ValueError('Schema2 is restricted to qualified KASLI04 basic native DMA')
        if observer.get('native_ddma_mode')!='playback' or any(v for k,v in observer.items() if k.startswith('native_ddma_') and k!='native_ddma_mode'):
            raise ValueError('KASLI04 profile must retain basic native DMA only')
        idle=observer['ddma_idle_qualification']
        if str(Path(idle).resolve()) not in pinned:
            raise ValueError('KASLI04 exact idle proof must be pinned')
        for name in data.get('pass_proofs',[]):
            proof=json.loads(Path(name).read_text());ext=proof.get('external_rx',{})
            if (proof.get('board')!='KASLI04' or proof.get('dna')!='0x006c440674704854' or
                proof.get('retained_restoration')!='PASS' or ext.get('restoration')!='PASS'):
                raise ValueError('KASLI04 proof lacks exact identity/both-board restoration')
        if not data.get('pass_proofs') or idle not in data['pass_proofs']:
            raise ValueError('KASLI04 idle proof must be a PASS proof')
    return data,verified


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--profile',type=Path,default=REPO/'diagnostics/drtio/profiles/kasli03-genesys-start-result.json')
    p.add_argument('--artifact-root',type=Path,default=Path('/srv/codex-hil-data/artiq-zynqmp'))
    p.add_argument('--output',type=Path,required=True,help='Fresh review/evidence directory')
    p.add_argument('--execute',action='store_true',help='Run guarded hardware session after preflight')
    a=p.parse_args();output=a.output.resolve()
    variables=dict(repo=str(REPO),artifacts=str(a.artifact_root.resolve()),
                   home=str(Path.home()),output=str(output))
    data,verified=validate(json.loads(a.profile.read_text()),variables)
    if output.exists():raise ValueError('Refusing to overwrite output directory')
    output.mkdir(parents=True)
    (output/'observer.json').write_text(json.dumps(data['observer'],indent=2)+'\n')
    (output/'command.json').write_text(json.dumps(data['argv'],indent=2)+'\n')
    result=dict(status='ARTIFACTS_VALIDATED',hardware_executed=False,artifacts=verified,
                profile_sha256=hashlib.sha256(a.profile.read_bytes()).hexdigest())
    (output/'review.json').write_text(json.dumps(result,indent=2)+'\n')
    preflight=subprocess.run(data['argv']+['--dry-run'],cwd=REPO,capture_output=True,text=True)
    (output/'preflight.log').write_text(preflight.stdout+preflight.stderr)
    if preflight.returncode:raise RuntimeError('Guarded-wrapper preflight failed; inspect preflight.log')
    if not a.execute:
        result['status']='PREFLIGHT_PASS_NO_HARDWARE_ACCESS'
        (output/'review.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps(dict(status=result['status'],review=str(output))))
        return
    # The parent owns the selected sorted leases across access/checks/restoration.
    with (output/'session.log').open('w') as log:
        child=subprocess.run(data['argv'],cwd=REPO,stdout=log,stderr=subprocess.STDOUT)
    passed=False
    if child.returncode==0:
        report=json.loads((output/'session/results.json').read_text())
        passed=report.get('status')=='PASS' and report.get('restoration')=='PASS'
        if data['schema']==2:
            passed=passed and report.get('retained_restoration')=='PASS' and report.get('external_rx',{}).get('restoration')=='PASS'
    result.update(status='WRAPPER_PASS' if passed else 'WRAPPER_FAIL',
                  hardware_executed=True,returncode=child.returncode)
    (output/'review.json').write_text(json.dumps(result,indent=2)+'\n')
    if not passed:raise SystemExit(child.returncode or 1)
    print(json.dumps(dict(status=result['status'],evidence=str(output/'session/results.json'))))

if __name__=='__main__':main()
