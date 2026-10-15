#!/usr/bin/env python3
"""Build upstream Rust AUX codec and AMD A53 test harness; LGPL-3.0-or-later."""
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
    p.add_argument('--csr-map',type=Path,required=True)
    p.add_argument('--external',action='store_true',help='Receive real remote requests; skip loopback self-test')
    p.add_argument('--tsc',action='store_true',help='ACK only observed hardware TSC loads; requires external')
    a=p.parse_args();
    if a.tsc and not a.external:p.error('--tsc requires --external')
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
    root=a.artiq_source.resolve()/'artiq/firmware'
    project=out/'rust';(project/'src').mkdir(parents=True,exist_ok=True)
    source=Path(__file__).with_name('lib.rs')
    (project/'src/lib.rs').write_bytes(source.read_bytes())
    manifest='''[package]
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
'''.replace('IO_PATH',json.dumps(str(root/'libio')))
    (project/'Cargo.toml').write_text(manifest)
    (project/'Cargo.lock').write_bytes(Path(__file__).with_name('firmware.Cargo.lock').read_bytes())
    env=os.environ.copy();env['ARTIQ_AUX_PROTOCOL']=str(root/'libproto_artiq/drtioaux_proto.rs')
    env['RUSTC_BOOTSTRAP']='1';env['RUSTUP_HOME']='/srv/codex-hil-data/artiq-zynqmp/rustup'
    result=subprocess.run(['cargo','+1.87.0','build','--locked','--release','--target','aarch64-unknown-none',
        '--manifest-path',str(project/'Cargo.toml')],env=env,capture_output=True,text=True,timeout=180)
    (out/'rust-build.log').write_text(result.stdout+result.stderr)
    if result.returncode:raise RuntimeError(result.stderr[-4000:])
    mapping=json.loads(a.csr_map.read_text())
    if 'aux_bridge_busy' not in mapping['registers']:p.error('AUX CSR map required')
    if a.tsc and not all('aux_'+n in mapping['registers'] for n in ('tsc_load_count','rt_reply_fault','rtio_error_flags')):p.error('Real satellite TSC/error CSR map required')
    header=['#pragma once']
    for name,register in mapping['registers'].items():
        if register['words']!=1:raise ValueError('Single-word CSR required')
        header.append('#define REG_'+name.upper()+' ((uintptr_t)'+hex(register['address'])+'u)')
    header.append('#define AUX_MEMORY ((uintptr_t)'+hex(mapping['aux_sram']['base'])+'u)')
    (out/'aux_regs.h').write_text('\n'.join(header)+'\n')
    bsp=Path('/srv/codex-hil-data/artiq-zynqmp/build-vivado/ethernet-reproduced/bsp')
    linker=bsp.parent/'app/src/lscript.ld'
    arm=Path('/srv/codex-hil-data/artiq-zynqmp/toolchains/arm-gnu/arm-gnu-toolchain-13.2.Rel1-x86_64-aarch64-none-elf')
    library=project/'target/aarch64-unknown-none/release/libgenesys_aux_codec.a'
    firmware=Path(__file__).with_name('firmware.c')
    elf=out/'aux-firmware.elf'
    cmd=[str(arm/'bin/aarch64-none-elf-gcc'),'-DSDT','-specs='+str(bsp/'Xilinx.spec'),
        *(['-DAUX_EXTERNAL'] if a.external else []),*(['-DAUX_TSC'] if a.tsc else []),'-I'+str(bsp/'include'),'-I'+str(out),'-Wall','-Wextra','-O2','-g',str(firmware),
        str(library),'-Wl,-T,'+str(linker),'-L'+str(bsp/'lib'),'-Wl,--start-group',
        '-lxilstandalone','-lxiltimer','-lxil','-lgcc','-lc','-Wl,--end-group','-o',str(elf)]
    result=subprocess.run(cmd,capture_output=True,text=True,timeout=120)
    (out/'link.log').write_text(result.stdout+result.stderr)
    if result.returncode:raise RuntimeError(result.stderr[-4000:])
    evidence={'kind':'FIRMWARE_BUILD_NOT_HARDWARE','status':'PASS',
        'mode':'external-tsc-down' if a.tsc else 'external-aux-down' if a.external else 'internal-loopback',
        'elf_sha256':hashlib.sha256(elf.read_bytes()).hexdigest(),
        'upstream_revision':subprocess.check_output(['git','-C',str(a.artiq_source),'rev-parse','HEAD'],text=True).strip(),
        'csr_map_sha256':hashlib.sha256(a.csr_map.read_bytes()).hexdigest(),
        'rust_source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'tsc_policy_sha256':hashlib.sha256(Path(__file__).with_name('tsc_ack_policy.h').read_bytes()).hexdigest(),
        'c_source_sha256':hashlib.sha256(firmware.read_bytes()).hexdigest()}
    (out/'results.json').write_text(json.dumps(evidence,indent=2)+'\n')
    print(json.dumps(evidence,indent=2))


if __name__=='__main__':main()
