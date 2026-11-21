#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Small isolated Rust target library with existing pinned local toolchain only."""
import argparse,json,os,subprocess,hashlib
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--artiq-source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--emit-stack-sizes',action='store_true');a=p.parse_args()
s=Path(__file__).resolve().parent;out=a.output.resolve();(out/'src').mkdir(parents=True,exist_ok=True)
root=a.artiq_source.resolve()/'artiq/firmware'
for src,dst in [('master_leaf_target.rs','lib.rs'),('master_leaf_codec.rs','master_leaf_codec.rs'),('master_control_codec.rs','master_control_codec.rs')]:
 (out/'src'/dst).write_bytes((s/src).read_bytes())
(out/'Cargo.lock').write_bytes((s/'firmware.Cargo.lock').read_bytes())
(out/'Cargo.toml').write_text('''[package]
name="genesys-aux-codec"
version="0.1.0"
edition="2015"
[lib]
crate-type=["staticlib"]
[profile.release]
panic="abort"
[dependencies]
failure={version="=0.1.1",default-features=false}
failure_derive={version="=0.1.1",default-features=false}
crc={version="=1.8.1",default-features=false}
io={path=IO_PATH,features=["byteorder"]}
'''.replace('IO_PATH',json.dumps(str(root/'libio'))))
env=dict(os.environ,RUSTUP_HOME='/srv/codex-hil-data/artiq-zynqmp/rustup',RUSTC_BOOTSTRAP='1',ARTIQ_AUX_PROTOCOL=str(root/'libproto_artiq/drtioaux_proto.rs'))
if a.emit_stack_sizes:env['RUSTFLAGS']=env.get('RUSTFLAGS','')+' -Zemit-stack-sizes'
r=subprocess.run(['cargo','+1.87.0','build','--offline','--locked','--release','--target','aarch64-unknown-none','--manifest-path',str(out/'Cargo.toml')],env=env,capture_output=True,text=True,timeout=180)
(out/'build.log').write_text(r.stdout+r.stderr)
if r.returncode:raise RuntimeError(r.stderr[-4000:])
lib=out/'target/aarch64-unknown-none/release/libgenesys_aux_codec.a'
(out/'results.json').write_text(json.dumps({'status':'ISOLATED_AARCH64_RUST_LIBRARY_COMPILE_PASS_NOT_EXECUTED','library_sha256':hashlib.sha256(lib.read_bytes()).hexdigest(),'emit_stack_sizes':a.emit_stack_sizes,'rustflags':env.get('RUSTFLAGS',''),'toolchain':'1.87.0','source_sha256':{str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in [s/'master_leaf_target.rs',s/'master_leaf_codec.rs',s/'master_control_codec.rs',root/'libproto_artiq/drtioaux_proto.rs',s/'firmware.Cargo.lock']}},indent=2)+'\n')
print('MASTER_LEAF_AARCH64_LIBRARY_PASS')
