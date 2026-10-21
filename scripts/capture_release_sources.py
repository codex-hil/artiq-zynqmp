#!/usr/bin/env python3
"""Capture current release input identities offline; LGPL-3.0-or-later.

A present-day snapshot does not establish the state used by an older build.
Tree traversal never follows symlinks. Git dirty patches are hashed, not saved.
"""
import argparse,hashlib,json,os,stat,subprocess
from pathlib import Path


def tree_snapshot(root):
    root=root.resolve();entries=[]
    def visit(directory):
        for path in sorted(directory.iterdir()):
            relative=path.relative_to(root).as_posix()
            before=path.lstat();mode=before.st_mode
            if stat.S_ISLNK(mode):
                entries.append(dict(path=relative,kind='symlink',target=os.readlink(path)))
            elif stat.S_ISDIR(mode):
                entries.append(dict(path=relative,kind='directory',mode=stat.S_IMODE(mode)))
                visit(path)
            elif stat.S_ISREG(mode):
                h=hashlib.sha256()
                with path.open('rb') as f:
                    for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
                after=path.lstat()
                if (before.st_ino,before.st_size,before.st_mtime_ns)!=(after.st_ino,after.st_size,after.st_mtime_ns):
                    raise ValueError('Input changed during capture: '+str(path))
                entries.append(dict(path=relative,kind='file',size=before.st_size,mode=stat.S_IMODE(mode),sha256=h.hexdigest()))
            else:raise ValueError('Unsupported input type: '+str(path))
    visit(root)
    encoded=json.dumps(entries,sort_keys=True,separators=(',',':')).encode()
    return dict(path=str(root),inventory_sha256=hashlib.sha256(encoded).hexdigest(),entries=entries)


def git_snapshot(root):
    root=root.resolve()
    def git(*args):return subprocess.check_output(['git','-C',str(root),*args])
    if Path(git('rev-parse','--show-toplevel').decode().strip()).resolve()!=root:
        raise ValueError('Expected exact repository root')
    patch=git('diff','--binary','HEAD','--')
    return dict(path=str(root),commit=git('rev-parse','HEAD').decode().strip(),
                tracked_status=git('status','--porcelain','--untracked-files=no').decode(),
                tracked_patch_sha256=hashlib.sha256(patch).hexdigest(),
                untracked_files='excluded; use --tree for a complete directory snapshot')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--git',action='append',default=[],metavar='NAME=PATH')
    p.add_argument('--tree',action='append',default=[],metavar='NAME=PATH')
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    if a.output.exists():raise ValueError('Refusing to overwrite manifest')
    result=dict(kind='current-input-snapshot-not-historical-build-proof',hardware_executed=False,git={},trees={})
    for group,items,capture in [('git',a.git,git_snapshot),('trees',a.tree,tree_snapshot)]:
        for spec in items:
            name,sep,path=spec.partition('=')
            if not sep or not name or name in result[group]:raise ValueError('Expected unique NAME=PATH')
            result[group][name]=capture(Path(path))
    if not result['git'] and not result['trees']:raise ValueError('No inputs')
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open('x') as f:f.write(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(status='SNAPSHOT_CAPTURED',output=str(a.output),tree_entries={k:len(v['entries']) for k,v in result['trees'].items()})))

if __name__=='__main__':main()
