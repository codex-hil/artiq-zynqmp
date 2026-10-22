#!/usr/bin/env python3
"""Read-only free-space admission for Genesys runtime windows; LGPL-3.0-or-later."""
import argparse,json,os
from pathlib import Path
MIN_BYTES=512*1024*1024
MIN_INODES=1024
AMD_SHARED=Path('/srv/codex-hil-data/toolchains/amd/shared')
class StorageAdmissionError(RuntimeError):
    def __init__(self,report):
        self.report=report
        super().__init__('Storage admission refused before hardware: '+json.dumps(report,sort_keys=True))

def inspect(paths):
    entries=[]
    for role,path in paths.items():
        requested=Path(path).resolve();anchor=requested
        while not anchor.exists():
            if anchor==anchor.parent:raise ValueError('No existing filesystem ancestor')
            anchor=anchor.parent
        stats=os.statvfs(anchor)
        entries.append(dict(role=role,path=str(requested),probe_path=str(anchor),
            available_bytes=stats.f_bavail*stats.f_frsize,available_inodes=stats.f_favail))
    passed=all(e['available_bytes']>=MIN_BYTES and e['available_inodes']>=MIN_INODES for e in entries)
    return dict(status='STORAGE_ADMISSION_PASS' if passed else 'STORAGE_ADMISSION_FAIL',hardware_executed=False,
        minimum_available_bytes=MIN_BYTES,minimum_available_inodes=MIN_INODES,entries=entries,
        limits='Point-in-time headroom check, not reservation or protection against concurrent disk consumption.')

def require_runtime_space(output,repo):
    report=inspect(dict(output=output,working_directory=repo,amd_home=AMD_SHARED/'home',amd_tmp=AMD_SHARED/'tmp',host_tmp=Path('/tmp')))
    if report['status']!='STORAGE_ADMISSION_PASS':raise StorageAdmissionError(report)
    return report

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output-directory',type=Path,required=True);p.add_argument('--repo',type=Path,default=Path(__file__).resolve().parents[1]);a=p.parse_args()
    report=inspect(dict(output=a.output_directory,working_directory=a.repo,amd_home=AMD_SHARED/'home',amd_tmp=AMD_SHARED/'tmp',host_tmp=Path('/tmp')))
    print(json.dumps(report,indent=2));return 0 if report['status']=='STORAGE_ADMISSION_PASS' else 1
if __name__=='__main__':raise SystemExit(main())
