#!/usr/bin/env python3
"""Bounded volatile candidate qualification with baseline restoration.

LGPL-3.0-or-later. Default is offline preflight; --execute requires exact
Genesys lease for every load/UART/network/test/restoration operation.
"""
import argparse,contextlib,fcntl,hashlib,json,os,re,signal,subprocess,sys,time
from pathlib import Path
from check_remote_rtio_build import check
REPO=Path(__file__).resolve().parents[1]
BASE=Path('/srv/codex-hil-data/artiq-zynqmp')
CABLE='210383B7F02DA'
LOCK=Path.home()/'.cache'/('genesys-'+CABLE+'.lock')


def preflight(manifest):
    if manifest.get('cable')!=CABLE or Path(manifest.get('lease','')).resolve()!=LOCK.resolve():
        raise ValueError('Wrong board identity/lease')
    files=manifest['files']
    required=['candidate_'+k for k in ('pl','csr','cpu0','worker','bridge','fsbl','pmu','ps_init')]+['restore_'+k for k in ('pl','cpu0','worker','bridge','fsbl','pmu','ps_init')]
    for key in required:
        entry=files[key];path=Path(entry['path'])
        if hashlib.sha256(path.read_bytes()).hexdigest()!=entry['sha256']:
            raise ValueError('Artifact hash mismatch: '+key)
    for prefix in ('candidate','restore'):
        worker=Path(files[prefix+'_worker']['path']);bridge=Path(files[prefix+'_bridge']['path'])
        ps=Path(files[prefix+'_fsbl']['path']).parents[2]
        if worker.name!='worker32.elf' or bridge!=worker.with_name('start64.elf'):
            raise ValueError('Worker pair layout mismatch')
        if Path(files[prefix+'_pmu']['path'])!=ps/'pmu-app/build/zynqmp_pmufw.elf' or Path(files[prefix+'_ps_init']['path'])!=ps/'sdt/psu_init.tcl':
            raise ValueError('PS input layout mismatch')
    # Re-run strict input/timing/DRC checks, not just a recorded PASS string.
    build=Path(files['candidate_pl']['path']).parent
    inputs=REPO/'evidence/dell-vivado-2026-10-21/pinned-ip-rebuild/inputs.json'
    check(build,json.loads(inputs.read_text()))
    return files


@contextlib.contextmanager
def lease(path=LOCK):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('a') as fd:
        try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise RuntimeError('BUSY: Genesys shared lease held elsewhere')
        yield fd


def lifecycle(cycle):
    result=dict(status='FAIL',restoration='NOT_RUN')
    try:
        result['candidate_ip']=cycle('candidate');result['status']='PASS'
    except BaseException as error:result['error']=str(error) or type(error).__name__
    finally:
        try:result['restored_ip']=cycle('restore');result['restoration']='PASS'
        except Exception as error:
            result.update(status='FAIL',restoration='FAIL',restoration_error=str(error))
    return result


def bounded(command,timeout,env,fd):
    proc=subprocess.Popen(command,cwd=REPO,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                          text=True,env=env,pass_fds=(fd,),start_new_session=True)
    try:
        text,_=proc.communicate(timeout=timeout)
        return proc.returncode,text
    except BaseException as error:
        try:os.killpg(proc.pid,signal.SIGTERM)
        except ProcessLookupError:pass
        try:text,_=proc.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            try:os.killpg(proc.pid,signal.SIGKILL)
            except ProcessLookupError:pass
            text,_=proc.communicate()
        if isinstance(error,subprocess.TimeoutExpired):error.output=text
        raise


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest',type=Path,default=REPO/'evidence/candidate-jtag-plan-2026-10-21/inputs.json')
    p.add_argument('--output',type=Path,required=True);p.add_argument('--execute',action='store_true')
    p.add_argument('--server');p.add_argument('--port');p.add_argument('--interface')
    p.add_argument('--rpc-fault-case',choices=['zero_descriptor_length','unsupported_return_tag','partial_float_eof'],help='One destructive RPC case; candidate immediately restored, never reused')
    p.add_argument('--extended',action='store_true',help='Candidate only: three cycles each of full CoreDMA and exception suites')
    p.add_argument('--artiq-python',default=str(BASE/'venvs/artiq-host/bin/python'))
    p.add_argument('--artiq-run',default=str(Path.home()/'.local/bin/artiq_run'))
    a=p.parse_args();files=preflight(json.loads(a.manifest.read_text()))
    out=a.output.resolve()
    if out.exists():raise ValueError('Use a fresh output directory')
    if a.execute and not all((a.server,a.port,a.interface)):p.error('Execution requires --server --port --interface')
    out.mkdir(parents=True)
    if not a.execute:
        (out/'results.json').write_text(json.dumps(dict(status='PREFLIGHT_PASS_NO_HARDWARE_ACCESS',hardware_executed=False),indent=2)+'\n')
        print('PREFLIGHT_PASS_NO_HARDWARE_ACCESS');return 0
    # No device opens, network accesses or subprocess hardware operations above.
    with lease() as held:
        # Recheck after obtaining ownership, before touching hardware.
        preflight(json.loads(a.manifest.read_text()))
        started=time.monotonic();stages={}
        env=os.environ.copy();env.pop('PYTHONPATH',None);env['GENESYS_LEASE_FD']=str(held.fileno())
        def run(stage,command,timeout):
            print(stage+' START',flush=True)
            try:code,text=bounded(command,timeout,env,held.fileno())
            except subprocess.TimeoutExpired as error:
                text=error.output or ""
                if isinstance(text,bytes):text=text.decode(errors="replace")
                (out/(stage+".log")).write_text(text)
                stages[stage]=dict(status='TIMEOUT');raise
            (out/(stage+'.log')).write_text(text);stages[stage]=dict(returncode=code)
            if code:raise RuntimeError(stage+' failed: '+text[-1500:])
            print(stage+' PASS',flush=True)
        def cycle(prefix):
            def path(name):return files[prefix+'_'+name]['path']
            ps=Path(path('fsbl')).parents[2];worker=Path(path('worker')).parent
            load=out/(prefix+'-load')
            run(prefix+'-load',[sys.executable,str(REPO/'scripts/load_rtio_runtime.py'),
                '--server',a.server,'--cable',CABLE,'--port',a.port,'--ps-export',str(ps),
                '--bitstream',path('pl'),'--worker',str(worker),'--cpu0',path('cpu0'),'--output',str(load)],240)
            loaded=json.loads((load/'results.json').read_text())
            if loaded.get('status')!='PASS':raise RuntimeError('Loader did not report PASS')
            ip=loaded['ip'];db=out/(prefix+'-device-db.py')
            text=(REPO/'examples/device_db_genesys.py').read_text()
            text,count=re.subn(r'([\"\']host[\"\']\s*:\s*[\"\'])\d+\.\d+\.\d+\.\d+([\"\'])',lambda m:m[1]+ip+m[2],text)
            if count!=1:raise ValueError('Expected one core address in copied database')
            db.write_text(text)
            run(prefix+'-debug',[a.artiq_python,str(REPO/'scripts/test_rtio_debug_hw.py'),'--ip',ip,'--device-db',str(db),'--artiq-run',a.artiq_run,'--output',str(out/(prefix+'-debug'))],240)
            if prefix=='candidate' and a.extended:
                run('candidate-core-dma',[a.artiq_python,str(REPO/'scripts/test_core_dma_hw.py'),
                    '--ip',ip,'--cycles','3','--output',str(out/'candidate-core-dma')],480)
                run('candidate-exceptions',[a.artiq_python,str(REPO/'scripts/test_kernel_exceptions_hw.py'),
                    '--ip',ip,'--cycles','3','--output',str(out/'candidate-exceptions')],480)
                run('candidate-post-errors-debug',[a.artiq_python,str(REPO/'scripts/test_rtio_debug_hw.py'),
                    '--ip',ip,'--device-db',str(db),'--artiq-run',a.artiq_run,
                    '--output',str(out/'candidate-post-errors-debug')],240)
            if prefix=='candidate' and a.rpc_fault_case:
                fault=out/'candidate-rpc-fault'
                run('candidate-rpc-fault',[a.artiq_python,str(REPO/'scripts/inject_rpc_fault.py'),
                    '--case',a.rpc_fault_case,'--ip',ip,'--device-db',str(db),'--output',str(fault)],90)
                observed=json.loads((fault/'results.json').read_text())
                if observed.get('status')!='FAULT_TERMINATION_OBSERVED_RESTORE_REQUIRED':
                    raise RuntimeError('RPC fault observation incomplete')
                run('candidate-rpc-terminal-event',['vivado-container','shell','-c','exec "$@"','bash',
                    '/srv/codex-hil-data/toolchains/amd/Xilinx/2025.2/Vivado/bin/xsdb',
                    str(REPO/'scripts/probe_rpc_failstop.tcl'),a.server,CABLE],30)
                return ip  # Read-only observation only; no kernel reuse before restoration.
            run(prefix+'-ethernet',[sys.executable,str(REPO/'scripts/test_ethernet_hw.py'),'--ip',ip,'--interface',a.interface,'--output',str(out/(prefix+'-ethernet.json'))],90)
            return ip
        # Convert external termination to an exception so restoration is attempted.
        old_handler=signal.signal(signal.SIGTERM,lambda *_:(_ for _ in ()).throw(RuntimeError('Termination requested')))
        try:result=lifecycle(cycle)
        finally:signal.signal(signal.SIGTERM,old_handler)
        result.update(kind='candidate-runtime-hardware',hardware_executed=True,lock=str(LOCK),cable=CABLE,
                      elapsed_seconds=round(time.monotonic()-started,3),stages=stages,extended=a.extended,rpc_fault_case=a.rpc_fault_case,
                      manifest_sha256=hashlib.sha256(a.manifest.read_bytes()).hexdigest())
        (out/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    return 0 if result['status']=='PASS' and result['restoration']=='PASS' else 1

if __name__=='__main__':raise SystemExit(main())
