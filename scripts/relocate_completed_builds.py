#!/usr/bin/env python3
"""Preserve selected completed ARTIQ builds on root storage; LGPL-3.0-or-later."""
import argparse,fcntl,gzip,hashlib,json,os,shutil,stat
from pathlib import Path
SOURCE=Path('/srv/codex-hil-data/artiq-zynqmp/build-vivado')
DESTINATION=Path('/home/codex-hil/.local/state/artiq-builds')
ALLOWED=('kernel-health-cpu0-20261022','rpc-parser-cpu0-20261022',
         'release-boot-firmware-2026-10-21','release-cpu0-2026-10-21',
         'ethernet-reproduced','fsbl-reproduced',
         'runtime-services-2025.2','eh-kernel-services','network-kernel-services',
         'network-kernel-services-final','rtio-kernel-services','services-reproduced',
         'runtime-ps-2025.2','fsbl-2025.2',
         'satellite-dma-credit4-route-2026-10-16','satellite-dma-route-v3-2026-10-16',
         'genesys-delay-metrics-route-2026-10-20','ethernet-2025.2')

def inventory(root):
    result={}
    for p in root.rglob('*'):
        key=str(p.relative_to(root));mode=stat.S_IMODE(p.lstat().st_mode)
        if p.is_symlink():result[key]=dict(symlink=os.readlink(p),mode=mode)
        elif p.is_file():result[key]=dict(sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size,mode=mode)
        elif p.is_dir():result[key]=dict(directory=True,mode=mode)
        else:raise ValueError('Unsupported special file: '+str(p))
    return result

def relocate(source,destination,report):
    if source.is_symlink() or not source.is_dir() or destination.exists() or destination.is_symlink() or report.exists():
        raise ValueError('Use unchanged directory and fresh destination/report')
    retired=source.with_name(source.name+'.relocation-retired')
    if retired.exists() or retired.is_symlink():raise ValueError('Retired path already exists')
    before=inventory(source);destination.parent.mkdir(parents=True,exist_ok=True)
    shutil.copytree(source,destination,symlinks=True)
    if inventory(destination)!=before or inventory(source)!=before:
        raise ValueError('Copy/source verification mismatch; original retained')
    # Publish verified backup before any original unlink; retains full manifest.
    data=dict(status='VERIFIED_COPY_READY',source=str(source),destination=str(destination),entries=len(before),inventory=before)
    report.parent.mkdir(parents=True,exist_ok=True)
    report.write_bytes(gzip.compress((json.dumps(data,sort_keys=True)+'\n').encode(),mtime=0))
    source.rename(retired)
    try:source.symlink_to(destination,target_is_directory=True)
    except BaseException:
        retired.rename(source);raise
    if inventory(source)!=before:raise ValueError('Published symlink verification failed; backup and retired original retained')
    shutil.rmtree(retired)
    data['status']='RELOCATED_VERIFIED_ORIGINAL_PATH_RETAINED'
    report.write_bytes(gzip.compress((json.dumps(data,sort_keys=True)+'\n').encode(),mtime=0))
    return {k:v for k,v in data.items() if k!='inventory'}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--name',choices=ALLOWED,action='append',required=True);p.add_argument('--execute',action='store_true');a=p.parse_args()
    if len(set(a.name))!=len(a.name):p.error('Duplicate build name')
    if not a.execute:
        print(json.dumps(dict(status='PLAN_ONLY',builds=[dict(source=str(SOURCE/n),destination=str(DESTINATION/n)) for n in a.name]),indent=2));return
    lock=Path.home()/'.cache/artiq-build-relocation.lock';lock.parent.mkdir(parents=True,exist_ok=True)
    with lock.open('a') as held:
        fcntl.flock(held,fcntl.LOCK_EX|fcntl.LOCK_NB)
        for name in a.name:
            print(name+' COPY_VERIFY_START',flush=True)
            result=relocate(SOURCE/name,DESTINATION/name,DESTINATION/(name+'.relocation.json.gz'))
            print(json.dumps(result),flush=True)
if __name__=='__main__':main()
