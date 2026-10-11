#!/usr/bin/env python3
"""Build reference vectors from unchanged upstream sources; LGPL-3.0-or-later."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--artiq-source',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    root=a.artiq_source.resolve()/'artiq/firmware'
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
    proto=root/'libproto_artiq/drtioaux_proto.rs'
    io=root/'libio'
    if not proto.is_file() or not (io/'Cargo.toml').is_file():p.error('ARTIQ firmware sources required')
    (out/'src').mkdir(exist_ok=True)
    source=Path(__file__).with_name('main.rs')
    (out/'src/main.rs').write_bytes(source.read_bytes())
    manifest='''[package]
name="genesys-aux-reference-vectors"
version="0.1.0"
edition="2015"
[dependencies]
failure={version="=0.1.1",default-features=false}
failure_derive={version="=0.1.1",default-features=false}
crc={version="=1.8.1",default-features=false}
io={path=IO_PATH,features=["byteorder"]}
'''.replace('IO_PATH',json.dumps(str(io)))
    (out/'Cargo.toml').write_text(manifest)
    (out/'Cargo.lock').write_bytes(Path(__file__).with_name('reference.Cargo.lock').read_bytes())
    env=os.environ.copy();env['ARTIQ_AUX_PROTOCOL']=str(proto)
    # Upstream libio's never_type feature remains needed; no source patches.
    env['RUSTC_BOOTSTRAP']='1'
    result=subprocess.run(['cargo','+stable','run','--locked','--manifest-path',str(out/'Cargo.toml')],
        env=env,capture_output=True,text=True,timeout=180)
    log=result.stdout+result.stderr
    (out/'build.log').write_text(log)
    if result.returncode:raise RuntimeError(log[-5000:])
    vectors={}
    for line in result.stdout.splitlines():
        if line.startswith('VECTOR '):_,name,data=line.split();vectors[name]=data
    if len(vectors)!=7 or 'TEST UPSTREAM_AUX_CODEC PASS' not in result.stdout:
        raise RuntimeError('Missing upstream acceptance output')
    evidence={'kind':'HOST_CODEC_TEST_NOT_FIRMWARE_OR_HARDWARE','status':'PASS',
        'vectors':vectors,'source_revision':subprocess.check_output(['git','-C',str(a.artiq_source),'rev-parse','HEAD'],text=True).strip(),
        'upstream_protocol_sha256':hashlib.sha256(proto.read_bytes()).hexdigest(),
        'reference_source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'log_sha256':hashlib.sha256(log.encode()).hexdigest(),
        'cargo_lock_sha256':hashlib.sha256((out/'Cargo.lock').read_bytes()).hexdigest()}
    (out/'results.json').write_text(json.dumps(evidence,indent=2)+'\n')
    print(json.dumps(evidence,indent=2))


if __name__=='__main__':main()
