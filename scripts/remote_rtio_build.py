#!/usr/bin/env python3
"""Prepare/submit/collect isolated Dell Vivado jobs; LGPL-3.0-or-later.

No board access. Normalization is a separate job whose output requires explicit
hash selection before a build; collection never approves IP changes automatically.
"""
import argparse,hashlib,json,re,shlex,shutil,subprocess,sys,difflib
from pathlib import Path
from check_remote_rtio_build import check
REMOTE_ROOT='/srv/nvme-fast-1/vivado-work'
HOST='codex-hil@192.168.2.7'
KEY=Path.home()/'.ssh/dell_build'
XCI='ip/platform_zynq_ultra_ps_e_0_0/platform_zynq_ultra_ps_e_0_0.xci'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path,value):path.write_text(json.dumps(value,indent=2)+'\n')
def relative(name):
    p=Path(name)
    if p.is_absolute() or '..' in p.parts or not re.fullmatch(r'[A-Za-z0-9_./-]+',name):
        raise ValueError('Unsafe input path')
    return p


def prepare(source,job,mode,normalized=None,expected=None):
    if mode not in ('normalize','build'):raise ValueError('Invalid mode')
    source=source.resolve();job=job.resolve()
    if job.exists():raise ValueError('Use a fresh job directory')
    if not re.fullmatch('[A-Za-z0-9_-]+',job.name):raise ValueError('Unsafe job name')
    generated=json.loads((source/'generation.json').read_text())
    if generated.get('status')!='HDL_GENERATED_NOT_SYNTHESIZED':raise ValueError('Expected generated HDL manifest')
    if bool(normalized)!=bool(expected):raise ValueError('Normalized XCI requires an explicit expected SHA-256')
    if normalized and mode!='build':raise ValueError('Normalization cannot use a preselected output')
    rows=[];sources=[];seen=set()
    for entry in generated['files']:
        name=entry['path'];path=relative(name)
        allowed=name in ('top.v','top.xdc','top.tcl','top_route.tcl','top_bitstream.tcl','csr-map.json',XCI) or (len(path.parts)==1 and path.suffix=='.init')
        if not allowed or name in seen:raise ValueError('Unexpected/duplicate generated input: '+name)
        seen.add(name);src=(source/path).resolve()
        if not src.is_relative_to(source) or sha(src)!=entry['sha256']:raise ValueError('Changed or external generated input: '+name)
        selected=Path(normalized).resolve() if normalized and name==XCI else src
        if normalized and name==XCI:
            if not re.fullmatch('[0-9a-f]{64}',expected) or sha(selected)!=expected:raise ValueError('Selected XCI hash mismatch')
            json.loads(selected.read_text())
        rows.append(dict(path=name,source_sha256=entry['sha256'],build_sha256=sha(selected)));sources.append(selected)
    if not {XCI,'top.v','top.xdc','top.tcl','top_route.tcl','top_bitstream.tcl','csr-map.json'}.issubset(seen):raise ValueError('Incomplete source input set')
    job.mkdir(parents=True)
    for row,src in zip(rows,sources):
        dest=job/row['path'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dest)
    shutil.copyfile(source/'generation.json',job/'generation.json')
    write(job/'inputs.json',dict(files=rows,scope='Generated local RTIO build inputs',selected_normalized_xci_sha256=expected))
    if mode=='normalize':
        (job/'normalize.tcl').write_text('create_project -force -name normalize -part xczu5ev-sfvc784-1-e\nread_ip {'+XCI+'}\nupgrade_ip [get_ips platform_zynq_ultra_ps_e_0_0]\ngenerate_target all [get_ips platform_zynq_ultra_ps_e_0_0]\ncreate_ip_run [get_ips platform_zynq_ultra_ps_e_0_0]\nlaunch_runs platform_zynq_ultra_ps_e_0_0_synth_1 -jobs 2\nwait_on_run platform_zynq_ultra_ps_e_0_0_synth_1\nif {[get_property PROGRESS [get_runs platform_zynq_ultra_ps_e_0_0_synth_1]] ne \"100%\"} {error \"PS IP synthesis failed\"}\nquit\n')
    remote=REMOTE_ROOT+'/'+job.name;entry='normalize.tcl' if mode=='normalize' else 'top.tcl'
    final='NORMALIZED_REVIEW_REQUIRED' if mode=='normalize' else 'FINISHED_CHECK_REPORTS'
    (job/'run.sh').write_text('''#!/bin/bash
set -u
cd %s || exit 2
printf 'WAITING_FOR_BUILD_LOCK\\n' > state.txt
exec 9>%s/.vivado-build.lock
flock 9 || exit 3
printf 'RUNNING\\n' > state.txt
/home/codex-hil/.local/bin/vivado -mode batch -nojournal -log vivado.log -source %s > console.log 2>&1
result=$?
printf '{"returncode":%%d}\\n' "$result" > exit.json
if [ "$result" = 0 ]; then printf '%s\\n' > state.txt; else printf 'FAILED\\n' > state.txt; fi
exit "$result"
'''%(shlex.quote(remote),shlex.quote(REMOTE_ROOT),entry,final))
    upload=[r['path'] for r in rows]+['generation.json','inputs.json','run.sh']+(['normalize.tcl'] if mode=='normalize' else [])
    metadata=dict(mode=mode,job=job.name,remote=remote,host=HOST,unit=job.name+'.service',upload_sha256={n:sha(job/n) for n in upload})
    write(job/'submission.json',metadata)
    return metadata


def prepare_ps(source,job):
    """Stage only Piotr's three PS Tcl inputs; no source checkout mutation."""
    source=source.resolve();job=job.resolve()
    if job.exists():raise ValueError('Use a fresh job directory')
    if not re.fullmatch('[A-Za-z0-9_-]+',job.name):raise ValueError('Unsafe job name')
    names=['vivado_script.tcl','migen_integration.tcl','zynq_ultra_ps_e_0.properties.tcl']
    for name in names:
        path=source/name
        if not path.is_file() or path.resolve()!=source/name:raise ValueError('Missing/linked PS source: '+name)
    job.mkdir(parents=True)
    for name in names:shutil.copyfile(source/name,job/name)
    remote=REMOTE_ROOT+'/'+job.name
    runner = '#!/bin/bash\n# PS source export; LGPL-3.0-or-later.\nset -u\ncd '+shlex.quote(remote)+' || exit 2\n'
    runner += "printf 'WAITING_FOR_BUILD_LOCK\\n' > state.txt\nexec 9>"+REMOTE_ROOT+"/.vivado-build.lock\nflock 9 || exit 3\nprintf 'RUNNING\\n' > state.txt\n"
    runner += '/home/codex-hil/.local/bin/vivado -mode batch -nojournal -log vivado.log -source vivado_script.tcl -tclargs local-rtio-dma > console.log 2>&1\nresult=$?\n'
    runner += "printf '{\"returncode\":%d}\\n' \"$result\" > exit.json\nif [ \"$result\" = 0 ]; then printf 'EXPORTED_REVIEW_REQUIRED\\n' > state.txt; else printf 'FAILED\\n' > state.txt; fi\nexit \"$result\"\n"
    (job/'run.sh').write_text(runner)
    names+=['run.sh']
    m=dict(mode='ps-export',job=job.name,remote=remote,host=HOST,unit=job.name+'.service',upload_sha256={n:sha(job/n) for n in names})
    write(job/'submission.json',m)
    return m


def export_hashes(m):
    code='import hashlib,json\nfrom pathlib import Path\nr=Path('+repr(m['remote'])+')\n'
    code+='assert isinstance(json.loads((r/"exit.json").read_text())["returncode"],int),"Job unfinished"\n'
    code+='print(json.dumps({str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in r.rglob("*") if p.is_file() and not p.is_symlink() and ".Xil" not in p.parts}))\n'
    hashes=json.loads(ssh('python3 -',script=code).stdout)
    for name in hashes:relative(name)
    return hashes


def metadata(job):
    m=json.loads((job/'submission.json').read_text())
    if not re.fullmatch('[A-Za-z0-9_-]+',m['job']) or m['remote']!=REMOTE_ROOT+'/'+m['job'] or m['host']!=HOST or m['unit']!=m['job']+'.service':raise ValueError('Invalid remote job metadata')
    if m['mode'] not in ('normalize','build','ps-export'):raise ValueError('Invalid job mode')
    for name in m['upload_sha256']:relative(name)
    return m


def ssh(command,*,script=None):
    return subprocess.run(['ssh','-i',str(KEY),'-o','BatchMode=yes','-o','ConnectTimeout=10',HOST,command],input=script,text=True,capture_output=True,check=True,timeout=120)


def remote_hashes(m,names,terminal=False):
    code='import hashlib,json\nfrom pathlib import Path\nr=Path('+repr(m['remote'])+')\n'
    if terminal:code+='assert isinstance(json.loads((r/"exit.json").read_text())["returncode"],int),"Job unfinished"\n'
    code+='print(json.dumps({n:hashlib.sha256((r/n).read_bytes()).hexdigest() for n in '+repr(names)+(' if (r/n).is_file()' if terminal else '')+'}))\n'
    return json.loads(ssh('python3 -',script=code).stdout)


def submit(job):
    m=metadata(job)
    for name,digest in m['upload_sha256'].items():
        if sha(job/name)!=digest:raise ValueError('Prepared job changed: '+name)
    # mkdir without -p deliberately refuses an existing remote job.
    ssh(shlex.join(['mkdir',m['remote']]))
    names='\n'.join(m['upload_sha256'])+'\n'
    subprocess.run(['rsync','-a','--files-from=-','-e','ssh -i '+shlex.quote(str(KEY))+' -o BatchMode=yes',str(job.resolve())+'/',HOST+':'+m['remote']+'/'],input=names,text=True,check=True,timeout=120)
    if remote_hashes(m,list(m['upload_sha256']))!=m['upload_sha256']:raise ValueError('Transfer hash mismatch')
    result=ssh(shlex.join(['systemd-run','--user','--unit='+m['job'],'/bin/bash',m['remote']+'/run.sh']))
    write(job/'submitted.json',dict(status='SUBMITTED_NOT_BUILD_PROOF',remote=m['remote'],transfer='PASS',service=result.stderr.strip()))


def collect(job,output):
    m=metadata(job)
    if output.exists():raise ValueError('Use a fresh result directory')
    names=list(m['upload_sha256'])+['exit.json','state.txt','console.log','vivado.log']
    if m['mode']=='build':names+=['top.bit','top_timing.rpt','top_drc.rpt','top_route_status.rpt']
    hashes=export_hashes(m) if m['mode']=='ps-export' else remote_hashes(m,names,True)
    output.mkdir(parents=True)
    subprocess.run(['rsync','-a','--files-from=-','-e','ssh -i '+shlex.quote(str(KEY))+' -o BatchMode=yes',HOST+':'+m['remote']+'/',str(output.resolve())+'/'],input='\n'.join(hashes)+'\n',text=True,check=True,timeout=120)
    for name,digest in hashes.items():
        if sha(output/name)!=digest:raise ValueError('Downloaded hash mismatch: '+name)
    write(output/'retrieval.json',dict(status='TRANSFER_PASS',sha256=hashes))
    code=json.loads((output/'exit.json').read_text())['returncode']
    if code:
        result=dict(status='REMOTE_VIVADO_FAILED',hardware_executed=False,vivado_returncode=code)
    else:
        try:
            if m['mode']=='ps-export':
                if any(hashes.get(n)!=h for n,h in m['upload_sha256'].items()):raise ValueError('PS export changed source input')
                required=['platform.xsa','mi_part.txt','mi_bd_cells.txt','mi_xci_files.txt','zynq_ultra_ps_e_0/pins.txt','zynq_ultra_ps_e_0/intf_pins.txt','zynq_ultra_ps_e_0/addr_segs.txt','zynq_ultra_ps_e_0/properties.txt']
                if any(n not in hashes or not (output/n).stat().st_size for n in required):raise ValueError('Incomplete PS export')
                refs=(output/'mi_xci_files.txt').read_text().splitlines()
                if not refs:raise ValueError('Missing exported IP references')
                for ref in refs:
                    prefix=m['remote']+'/'
                    if not ref.startswith(prefix):raise ValueError('External exported IP reference')
                    name=str(relative(ref[len(prefix):]))
                    if name not in hashes or not name.endswith('.xci'):raise ValueError('Missing exported IP file')
                result=dict(status='PS_EXPORTED_REVIEW_REQUIRED',hardware_executed=False,files_verified=len(hashes),scope='Export/transfer/input hashes only; parameter/HDL/SDT comparison required')
            elif m['mode']=='build':
                result=check(output,json.loads((job/'inputs.json').read_text()))
            else:
                changed=[name for name,old in m['upload_sha256'].items() if hashes[name]!=old]
                result=dict(status='NORMALIZED_REVIEW_REQUIRED',hardware_executed=False,changed_inputs=changed,xci_sha256=hashes[XCI])
                (output/'xci.diff').write_text(''.join(difflib.unified_diff((job/XCI).read_text().splitlines(True),(output/XCI).read_text().splitlines(True),fromfile='input.xci',tofile='normalized.xci')))
                if any(name!=XCI for name in changed):raise ValueError('Normalization changed an unexpected input')
        except (ValueError,KeyError,OSError) as error:
            result=dict(status='RESULT_CHECK_FAILED',hardware_executed=False,error=str(error))
    write(output/'results.json',result)
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    q=sub.add_parser('prepare');q.add_argument('--source',type=Path,required=True);q.add_argument('--job',type=Path,required=True);q.add_argument('--mode',choices=['normalize','build'],required=True);q.add_argument('--normalized-xci',type=Path);q.add_argument('--expected-xci-sha256')
    q=sub.add_parser('prepare-ps');q.add_argument('--source',type=Path,required=True);q.add_argument('--job',type=Path,required=True)
    q=sub.add_parser('submit');q.add_argument('--job',type=Path,required=True)
    q=sub.add_parser('status');q.add_argument('--job',type=Path,required=True)
    q=sub.add_parser('collect');q.add_argument('--job',type=Path,required=True);q.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    if a.command=='prepare':print(json.dumps(prepare(a.source,a.job,a.mode,a.normalized_xci,a.expected_xci_sha256),indent=2))
    elif a.command=='prepare-ps':print(json.dumps(prepare_ps(a.source,a.job),indent=2))
    elif a.command=='submit':submit(a.job);print('SUBMITTED_NOT_BUILD_PROOF')
    elif a.command=='status':
        m=metadata(a.job);print(ssh('cd '+shlex.quote(m['remote'])+' && cat state.txt').stdout,end='')
    else:
        result=collect(a.job,a.output);print(json.dumps(result,indent=2))
        if result['status'] in ('REMOTE_VIVADO_FAILED','RESULT_CHECK_FAILED'):raise SystemExit(1)

if __name__=='__main__':main()
