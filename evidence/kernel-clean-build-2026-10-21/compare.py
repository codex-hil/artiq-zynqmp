"""Offline ELF32 comparison for this checkpoint; LGPL-3.0-or-later."""
import hashlib,json,struct
from pathlib import Path
BASE=Path('/srv/codex-hil-data/artiq-zynqmp')
def inspect(path):
    data=path.read_bytes()
    if data[:6]!=b'\x7fELF\x01\x01':raise ValueError('Expected little-endian ELF32')
    offset=struct.unpack_from('<I',data,28)[0]
    size,count=struct.unpack_from('<HH',data,42)
    segments=[];payloads=[]
    for index in range(count):
        typ,pos,va,pa,fs,ms,flags,align=struct.unpack_from('<8I',data,offset+index*size)
        if typ!=1:continue
        payload=data[pos:pos+fs]
        if len(payload)!=fs:raise ValueError('Truncated load segment')
        segments.append(dict(vaddr=va,paddr=pa,filesz=fs,memsz=ms,flags=flags,sha256=hashlib.sha256(payload).hexdigest()))
        payloads.append(payload)
    return dict(path=str(path),sha256=hashlib.sha256(data).hexdigest(),load_segments=segments),payloads
pairs=[inspect(BASE/'build'/f'release-worker-canonical-{label}-2026-10-21/worker32.elf') for label in 'ab']
a,b=pairs
result=dict(status='BUILD_PASS_REPRODUCIBILITY_FAIL',hardware_executed=False,source_commit='35518ff',
    scope='Two clean detached worktrees, fresh output directories; shared installed toolchains and Cargo cache; not a fresh-host test',
    binaries=[a[0],b[0]],load_segments_equal=a[0]['load_segments']==b[0]['load_segments'],
    load_differing_bytes=sum(sum(x!=y for x,y in zip(left,right))+abs(len(left)-len(right)) for left,right in zip(a[1],b[1])),
    tool_manifest_sha256=hashlib.sha256((BASE/'toolchains/abi-verified/manifest.json').read_bytes()).hexdigest(),
    cargo_lock_sha256=hashlib.sha256((BASE/'work/release-repro-2026-10-21/boards/genesys_zu-5ev/3_kernel/Cargo.lock').read_bytes()).hexdigest(),
    csr_sha256=hashlib.sha256((BASE/'build-vivado/genesys-rtio-dma/migen-build/csr-map.json').read_bytes()).hexdigest(),
    environment=dict(RUSTUP_HOME=str(BASE/'rustup'),KERNEL_REMAP_PATHS='1'),
    retained_qualified_worker_sha256='393fea490a45f3f3140de1a078313ad963bb3c429c32f6fe16012bf29cd305e7')
Path(__file__).with_name('results.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
