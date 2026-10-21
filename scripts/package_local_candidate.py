#!/usr/bin/env python3
"""Package exact JTAG-qualified candidate artifacts, not cold-boot proof.

LGPL-3.0-or-later. No hardware/card access. Verifies proof/manifest binding and
that the SD bridge embeds the tested worker load image before invoking bootgen.
"""
import argparse,hashlib,json,struct,subprocess,sys,shutil
from pathlib import Path
REPO=Path(__file__).resolve().parents[1]


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def loads(data):
    if data[:4]!=b'\x7fELF' or data[5:7]!=b'\x01\x01' or data[4] not in (1,2):raise ValueError('Expected little-endian ELF')
    wide=data[4]==2
    fmt='<HHIQQQIHHHHHH' if wide else '<HHIIIIIHHHHHH'
    fields=struct.unpack_from(fmt,data,16)
    kind,machine,version,entry,offset,_,_,_,size,count,*_=fields
    expected=56 if wide else 32
    if kind!=2 or version!=1 or size!=expected or offset+size*count>len(data):raise ValueError('Invalid ELF headers')
    segments=[]
    for i in range(count):
        values=struct.unpack_from('<II6Q' if wide else '<8I',data,offset+i*size)
        if wide:typ,flags,pos,va,pa,fs,ms,align=values
        else:typ,pos,va,pa,fs,ms,flags,align=values
        if typ!=1:continue
        if fs>ms or pos+fs>len(data):raise ValueError('Invalid ELF load segment')
        segments.append(dict(address=pa,vaddr=va,filesz=fs,memsz=ms,flags=flags,payload=data[pos:pos+fs]))
    return machine,entry,segments


def match_worker(worker,bridge):
    machine,entry,w=loads(worker);bm,be,b=loads(bridge)
    if machine!=40 or entry!=0x20200000 or len(w)!=1 or w[0]['address']!=0x20200000 or w[0]['address']+w[0]['memsz']>0x20400000:
        raise ValueError('Unexpected tested worker layout')
    if bm!=183 or be!=0x20000000 or len(b)!=2:raise ValueError('Unexpected SD bridge layout')
    if b[0]['address']!=0x20000000 or b[0]['address']+b[0]['memsz']>=0x200ff000 or not b[0]['flags']&1:
        raise ValueError('Bridge overlaps mailbox or lacks executable entry')
    if b[1]['address']!=0x20200000 or b[1]['payload']!=w[0]['payload'] or b[1]['memsz']!=w[0]['filesz']:
        raise ValueError('SD bridge worker payload differs from tested image')
    return dict(status='EXACT_TESTED_WORKER_PAYLOAD',address='0x20200000',bytes=w[0]['filesz'],sha256=hashlib.sha256(w[0]['payload']).hexdigest())


def verify_proof(manifest_path,proof_path):
    manifest=json.loads(manifest_path.read_text());proof=json.loads(proof_path.read_text())
    if proof.get('status')!='PASS' or proof.get('restoration')!='PASS' or not proof.get('hardware_executed') or not proof.get('extended'):
        raise ValueError('Extended hardware/restoration PASS required')
    if proof.get('manifest_sha256')!=sha(manifest_path) or proof.get('cable')!='210383B7F02DA' or manifest.get('cable')!=proof['cable']:
        raise ValueError('Physical proof does not bind this candidate')
    for name,item in manifest['files'].items():
        if sha(Path(item['path']))!=item['sha256']:raise ValueError('Changed artifact: '+name)
    return manifest['files']


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest',type=Path,default=REPO/'evidence/candidate-jtag-plan-2026-10-21/inputs.json')
    p.add_argument('--proof',type=Path,default=REPO/'evidence/candidate-extended-hardware-2026-10-21/results.json')
    p.add_argument('--sd-bridge',type=Path,required=True);p.add_argument('--sd-bridge-sha256',required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--bootgen',default='bootgen');a=p.parse_args()
    if a.output.exists():raise ValueError('Use a fresh package directory')
    files=verify_proof(a.manifest,a.proof)
    if sha(a.sd_bridge)!=a.sd_bridge_sha256:raise ValueError('SD bridge digest mismatch')
    embedded=match_worker(Path(files['candidate_worker']['path']).read_bytes(),a.sd_bridge.read_bytes())
    cmd=[sys.executable,str(REPO/'scripts/build_boot_image.py'),'--fsbl',files['candidate_fsbl']['path'],
         '--pmufw',files['candidate_pmu']['path'],'--bitstream',files['candidate_pl']['path'],
         '--application',files['candidate_cpu0']['path'],'--worker-boot',str(a.sd_bridge.resolve()),
         '--bootgen',a.bootgen,'--output-dir',str(a.output.resolve())]
    subprocess.run(cmd,check=True)
    headers=subprocess.run([a.bootgen,'-arch','zynqmp','-read',str(a.output.resolve()/'boot.bin'),'pht'],capture_output=True,text=True,check=True)
    (a.output/'partition-headers.txt').write_text(headers.stdout+headers.stderr)
    shutil.copyfile(a.output/'boot.bin',a.output/'BOOT.BIN')
    report=dict(status='PACKAGED_JTAG_QUALIFIED_INPUTS_COLD_BOOT_NOT_RUN',hardware_executed=False,cold_boot='NOT_RUN',
                manifest_sha256=sha(a.manifest),extended_jtag_proof_sha256=sha(a.proof),sd_bridge_sha256=sha(a.sd_bridge),
                worker_embedding=embedded,boot_bin_sha256=sha(a.output/'BOOT.BIN'),
                limits='Input proof/hash binding only; this is not signed provenance or a cold SD boot test. Original PS/PL source provenance remains separately documented.')
    (a.output/'release.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

if __name__=='__main__':main()
