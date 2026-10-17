"""Copy host package and fix DMA cursor unwind locally; LGPL-3.0-or-later."""
import argparse,hashlib,json,shutil
from pathlib import Path


def prepare(source,output):
    source=Path(source).resolve();output=Path(output).resolve()
    if output.exists():raise ValueError('Refusing to overwrite host overlay')
    original=(source/'coredevice/dma.py').read_text()
    old='        dma_record_stop(now_mu(), self.enable_ddma) # see above\n        at_mu(self.saved_now_mu)'
    if original.count(old)!=1:raise ValueError('Host DMA shape changed; review overlay')
    changed=original.replace(old,'        try:\n            dma_record_stop(now_mu(), self.enable_ddma)\n        finally:\n            at_mu(self.saved_now_mu)')
    shutil.copytree(source,output/'artiq',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    (output/'artiq/coredevice/dma.py').write_text(changed)
    result=dict(kind='isolated-host-overlay-not-hardware',source=str(source),
        original_sha256=hashlib.sha256(original.encode()).hexdigest(),
        dma_sha256=hashlib.sha256(changed.encode()).hexdigest())
    result['files_sha256']={str(p.relative_to(output)):hashlib.sha256(p.read_bytes()).hexdigest()
        for p in (output/'artiq').rglob('*') if p.is_file()}
    (output/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


def validate(output):
    output=Path(output).resolve()
    proof=json.loads((output/'results.json').read_text())
    actual={str(p.relative_to(output)):hashlib.sha256(p.read_bytes()).hexdigest()
        for p in (output/'artiq').rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}
    if not proof.get('files_sha256') or actual!=proof['files_sha256']:
        raise ValueError('Stale or incomplete host overlay')
    if actual.get('artiq/coredevice/dma.py')!=proof['dma_sha256']:
        raise ValueError('Host DMA overlay mismatch')
    return proof

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();print(json.dumps(prepare(a.source,a.output)))
