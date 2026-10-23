#!/usr/bin/env python3
"""Read-only free-space admission for Genesys runtime windows; LGPL-3.0-or-later."""
import argparse,json,os,tempfile
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

def runtime_paths(output,repo):
    return dict(output=output,working_directory=repo,amd_home=AMD_SHARED/'home',amd_tmp=AMD_SHARED/'tmp',host_tmp=Path('/tmp'))

def require_runtime_space(output,repo):
    report=inspect(runtime_paths(output,repo))
    if report['status']!='STORAGE_ADMISSION_PASS':raise StorageAdmissionError(report)
    return report

# Reserve real allocated blocks, not sparse file length. Never pass these FDs to
# children: process death releases unlinked files automatically.
RESTORE_RESERVE_BYTES=768*1024*1024
class RestoreReserve:
    def __init__(self,paths,amount=RESTORE_RESERVE_BYTES):
        if type(amount) is not int or amount<=0:raise ValueError('Positive reserve size required')
        self.paths=paths;self.amount=amount;self.fds=[];self.entries=[];self.released=False
    @staticmethod
    def device(path):return os.stat(path).st_dev
    def __enter__(self):
        seen=set()
        try:
            for role,path in self.paths.items():
                anchor=Path(path).resolve()
                while not anchor.exists():anchor=anchor.parent
                if not anchor.is_dir():anchor=anchor.parent
                device=self.device(anchor)
                if device in seen:continue
                stats=os.statvfs(anchor)
                if stats.f_bavail*stats.f_frsize<self.amount+MIN_BYTES or stats.f_favail<MIN_INODES:
                    raise RuntimeError('Insufficient space for restore reserve plus normal admission: '+str(anchor))
                fd,name=tempfile.mkstemp(prefix='.artiq-restore-reserve-',dir=anchor)
                self.fds.append(fd)
                os.unlink(name)
                os.posix_fallocate(fd,0,self.amount)
                os.fsync(fd)
                allocated=os.fstat(fd).st_blocks*512
                if allocated<self.amount:raise RuntimeError('Reserve allocation is sparse/insufficient')
                self.entries.append(dict(role=role,path=str(anchor),device=device,bytes=self.amount,allocated_bytes=allocated))
                seen.add(device)
            return self
        except BaseException:
            self.release();raise
    def release(self):
        errors=[]
        for fd in self.fds:
            try:os.close(fd)
            except OSError as e:errors.append(str(e))
        self.fds=[];self.released=True
        if errors:raise RuntimeError('Reserve close failed: '+str(errors))
    def report(self):
        return dict(status='RELEASED_FOR_RESTORATION' if self.released else 'ALLOCATED',entries=self.entries,
                    limits='Allocated unlinked blocks released before restore; not protection against concurrent consumption after release, inode exhaustion, quotas, I/O faults or SIGKILL during restoration.')
    def __exit__(self,*args):self.release()

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output-directory',type=Path,required=True);p.add_argument('--repo',type=Path,default=Path(__file__).resolve().parents[1]);a=p.parse_args()
    report=inspect(dict(output=a.output_directory,working_directory=a.repo,amd_home=AMD_SHARED/'home',amd_tmp=AMD_SHARED/'tmp',host_tmp=Path('/tmp')))
    print(json.dumps(report,indent=2));return 0 if report['status']=='STORAGE_ADMISSION_PASS' else 1
if __name__=='__main__':raise SystemExit(main())
