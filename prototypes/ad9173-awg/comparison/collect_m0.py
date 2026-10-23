"""Read-only source inventory and separate golden artifact snapshot; no device access."""
import hashlib,json,subprocess,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[2]
ART=Path('/srv/codex-hil-data/artiq-zynqmp/artifacts/alinx-phaser-m0-20261023')
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def git(p,*args):return subprocess.check_output(['git','-C',str(p),*args],text=True).strip()
def save(name,obj): (ROOT/name).write_text(json.dumps(obj,indent=2)+'\n') # JSON is YAML 1.2
repos=[('artiq','/srv/codex-hil-data/artiq-zynqmp/reference/artiq','https://github.com/m-labs/artiq','LGPL-3.0; see LICENSE and per-file exceptions'),('phaser','/home/codex-hil/open-miqro-awg/upstream/phaser','https://github.com/quartiq/phaser','GPL-3.0-or-later (README.md)'),('misoc','/srv/codex-hil-data/artiq-zynqmp/reference/misoc','https://github.com/m-labs/misoc','BSD-2-Clause (LICENSE)')]
deps=json.loads((ROOT.parent/'dependencies.json').read_text())['git_dependencies']
for d in deps:repos.append((d['name'],d['local_reference'],d['url'],'See recorded license file; not relicensed'))
records=[]
for name,path,url,license in repos:
    p=Path(path); licenses=[x for x in p.iterdir() if x.is_file() and x.name.lower().startswith(('license','copying'))]
    records.append(dict(name=name,path=path,upstream=url,commit=git(p,'rev-parse','HEAD'),tracked_diff=git(p,'diff','--stat','HEAD'),license=license,license_files={x.name:sha(x) for x in licenses}))
source=Path('/home/codex-hil/trenz-bringup/jesd')
manifest=json.loads((source/'payload-fixed-build-manifest.json').read_text())
ART.mkdir(parents=True,exist_ok=True)
files={}
# Preserve named historical evidence and all local HDL/Tcl/Python/init build inputs.
selected=set(source.glob('*.py'))|set(source.glob('*.v'))|set(source.glob('*.tcl'))|set(source.glob('*.init'))
selected|={source/n for n in ['fabric_spi_slow6144.bit','payload-fixed-build-manifest.json','slow6144-debug-build.log','profile-slow6144.json','payload-rf-pass-2026-10-21.json','two-tone-149-151-2026-10-21.json']}
for p in sorted(selected):
    if not p.is_file():raise FileNotFoundError(p)
    digest=sha(p); dest=ART/p.name
    if dest.exists():assert sha(dest)==digest, f'Refuse to overwrite snapshot: {dest}'
    else:shutil.copy2(p,dest)
    assert sha(dest)==digest
    files[p.name]={'sha256':digest,'bytes':p.stat().st_size,'historical_hash_matches':digest==manifest['sha256'][p.name] if p.name in manifest['sha256'] else None}
assert files['fabric_spi_slow6144.bit']['historical_hash_matches']
save('source_manifest.yaml',{'date':'2026-10-23','format':'JSON-compatible YAML 1.2','sources':records,'port_commit':git(REPO,'rev-parse','HEAD'),'golden':{'snapshot':str(ART),'files':files,'warning':'Historical RF evidence only; present powered board state not queried. Hash mismatch on source means historical provenance needs review; bitstream match required.'}})
print(json.dumps({'snapshot_files':len(files),'golden_bitstream_verified':True,'historical_source_mismatches':[n for n,v in files.items() if v['historical_hash_matches'] is False]}))
