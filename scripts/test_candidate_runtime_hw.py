#!/usr/bin/env python3
"""Bounded volatile candidate qualification with baseline restoration.

LGPL-3.0-or-later. Default is offline preflight; --execute requires exact
Genesys lease for every load/UART/network/test/restoration operation.
"""
import argparse,contextlib,fcntl,hashlib,json,os,re,signal,subprocess,sys,time
from pathlib import Path
from check_remote_rtio_build import check
from check_hw_storage import require_runtime_space
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
    if manifest.get('dma_observer'):
        from dma_observer_candidate import preflight as observer_candidate_preflight
        inputs=observer_candidate_preflight(manifest['dma_observer'],files,REPO)
    check(build,json.loads(inputs.read_text()))
    return files


def ocm_preflight(path,files):
    from check_ocm_image import check as check_ocm
    data=json.loads(path.read_text())
    for key in ('elf','symbols','ps_init'):
        item=data[key]
        if hashlib.sha256(Path(item['path']).read_bytes()).hexdigest()!=item['sha256']:
            raise ValueError('Changed OCM input: '+key)
    if data['ps_init']!=files['candidate_ps_init']:raise ValueError('OCM PS setup differs from selected candidate')
    required_scripts={'scripts/run_ocm_environment.py','scripts/run_ocm_environment.tcl'}
    if set(data.get('script_sha256',{}))!=required_scripts:raise ValueError('Missing OCM script pins')
    for name,digest in data['script_sha256'].items():
        if hashlib.sha256((REPO/name).read_bytes()).hexdigest()!=digest:raise ValueError('Changed OCM loader/capture script')
    check_ocm(Path(data['elf']['path']).read_bytes(),Path(data['symbols']['path']).read_text())
    return data


OBSERVER_SCRIPTS={'scripts/test_candidate_runtime_hw.py','scripts/run_trained_observer.py',
 'scripts/run_trained_observer.tcl','scripts/collect_fsbl_entry.tcl','scripts/check_el3_observer.py',
 'scripts/check_fsbl_observer_entry.py','scripts/package_local_candidate.py','scripts/check_hw_storage.py',
 'scripts/reset_genesys_ps.tcl','scripts/run_boot_firmware.tcl','scripts/load_rtio_runtime.py',
 'scripts/prepare_local_rtio.tcl','scripts/run_kernel_worker.tcl','scripts/run_a53_runtime.tcl',
 'scripts/program_genesys_pl.tcl'}
EXCEPTION_OBSERVER_EXTRA={'scripts/load_el3_exception_observer.tcl','scripts/check_el3_exception_observer.py','scripts/inject_rpc_fault.py','scripts/verify_el3_brk_capture.py'}
def observer_preflight(path,files):
    from check_el3_observer import check as check_observer
    from check_fsbl_observer_entry import descriptor
    info=json.loads(path.read_text())
    for name in ('elf','symbols'):
        item=info[name]
        if hashlib.sha256(Path(item['path']).read_bytes()).hexdigest()!=item['sha256']:
            raise ValueError('Changed observer input: '+name)
    if type(info.get('exception_brk',False)) is not bool or (info.get('exception_brk') and not info.get('exception_observer')):raise ValueError('BRK requires exception-aware observer')
    if type(info.get('exception_observer',False)) is not bool or (info.get('exception_observer') and (info.get('controls_only') or info.get('definitions_only'))):raise ValueError('Invalid exception observer mode')
    if type(info.get('controls_only',False)) is not bool or (info.get('controls_only') and info.get('definitions_only')):raise ValueError('Invalid observation mode')
    if type(info.get('definitions_only',False)) is not bool:raise ValueError('Invalid definitions-only mode')
    if info['fsbl_sha256']!=files['candidate_fsbl']['sha256']:
        raise ValueError('Observer FSBL pin mismatch')
    required_scripts=OBSERVER_SCRIPTS|(EXCEPTION_OBSERVER_EXTRA if info.get('exception_observer') else set())
    if info.get('peripheral_inputs'):
        if not info.get('exception_observer') or info.get('exception_brk'):
            raise ValueError('Peripheral window requires normal exception observer')
        from capture_peripheral_dma_state import SCRIPTS, preflight
        item=info['peripheral_inputs']
        if hashlib.sha256(Path(item['path']).read_bytes()).hexdigest()!=item['sha256']:
            raise ValueError('Changed peripheral window inputs')
        preflight(Path(item['path']))
        required_scripts |= SCRIPTS | {'scripts/check_boot_peripheral_window.py'}
    if info.get('master_inputs'):
        if not info.get('peripheral_inputs'):
            raise ValueError('Master window requires peripheral window')
        from collect_boot_masters import SCRIPTS as MASTER_SCRIPTS, preflight as master_preflight
        item=info['master_inputs']
        if hashlib.sha256(Path(item['path']).read_bytes()).hexdigest()!=item['sha256']:
            raise ValueError('Changed master window inputs')
        master_preflight(Path(item['path']))
        required_scripts |= MASTER_SCRIPTS
    if info.get('no_master_inputs'):
        if not info.get('exception_observer') or info.get('exception_brk') or not info.get('master_inputs'):
            raise ValueError('No-master image requires complete normal observer window')
        from no_master_candidate import preflight as no_master_preflight, SCRIPTS as NO_MASTER_SCRIPTS
        item=info['no_master_inputs']
        if hashlib.sha256(Path(item['path']).read_bytes()).hexdigest()!=item['sha256']:raise ValueError('Changed no-master inputs')
        no_master_preflight(Path(item['path']),REPO)
        required_scripts |= NO_MASTER_SCRIPTS
    if info.get('model_inputs'):
        if not info.get('no_master_inputs'):raise ValueError('Model requires qualified no-master window')
        from check_ddr_ocm_model import preflight as model_preflight, SCRIPTS as MODEL_SCRIPTS
        item=info['model_inputs']
        if hashlib.sha256(Path(item['path']).read_bytes()).hexdigest()!=item['sha256']:raise ValueError('Changed model inputs')
        model_preflight(Path(item['path']),REPO)
        required_scripts |= MODEL_SCRIPTS
    if info.get('pmu_boundary_inputs'):
        if not info.get('no_master_inputs') or info.get('model_inputs'):raise ValueError('PMU telemetry requires no-master normal window without model')
        from pmu_boundary_candidate import preflight as pmu_preflight, SCRIPTS as PMU_SCRIPTS
        item=info['pmu_boundary_inputs']
        if hashlib.sha256(Path(item['path']).read_bytes()).hexdigest()!=item['sha256']:raise ValueError('Changed PMU diagnostic inputs')
        pmu_preflight(Path(item['path']),REPO)
        required_scripts |= PMU_SCRIPTS
    if set(info.get('script_sha256',{}))!=required_scripts:
        raise ValueError('Missing observer execution pins')
    for name,digest in info['script_sha256'].items():
        if hashlib.sha256((REPO/name).read_bytes()).hexdigest()!=digest:
            raise ValueError('Changed observer execution dependency: '+name)
    if info.get('exception_observer'):
        from check_el3_exception_observer import check as check_observer
    check_observer(Path(info['elf']['path']).read_bytes())
    descriptor(Path(files['candidate_fsbl']['path']).read_bytes(),Path(info['symbols']['path']).read_text())
    return info


SPD_SCRIPTS={'scripts/check_hw_storage.py','scripts/test_candidate_runtime_hw.py','scripts/load_rtio_runtime.py',
 'scripts/reset_genesys_ps.tcl','scripts/run_boot_firmware.tcl','scripts/prepare_local_rtio.tcl',
 'scripts/run_kernel_worker.tcl','scripts/run_a53_runtime.tcl','scripts/program_genesys_pl.tcl',
 'scripts/decode_fsbl_spd_log.py','scripts/check_ddr4_spd_crc.py','scripts/decode_ddr4_spd.py'}
def spd_preflight(manifest,files):
    info=manifest.get('fsbl_spd',{})
    if info.get('fsbl_sha256')!=files['candidate_fsbl']['sha256']:
        raise ValueError('Missing or inconsistent diagnostic FSBL pin')
    if set(info.get('script_sha256',{}))!=SPD_SCRIPTS:raise ValueError('Missing SPD script pins')
    for name,digest in info['script_sha256'].items():
        if hashlib.sha256((REPO/name).read_bytes()).hexdigest()!=digest:raise ValueError('Changed SPD execution/parser script: '+name)
    if b'SPD_BASE_BEGIN bytes=128' not in Path(files['candidate_fsbl']['path']).read_bytes():
        raise ValueError('Selected FSBL lacks diagnostic SPD marker')
    return info


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
    p.add_argument('--fsbl-spd',action='store_true',help='Require pinned diagnostic FSBL and strict UART SPD/CRC capture before runtime tests')
    p.add_argument('--trained-observer-manifest',type=Path,help='FSBL-trained register-only observation, then mandatory normal restoration')
    p.add_argument('--ocm-manifest',type=Path,help='OCM observation instead of normal candidate runtime; always restores normal baseline')
    p.add_argument('--expect-kernel-state',action='store_true',help='Assert new candidate idle/waiting-rpc/restart-required; requires one fault case')
    p.add_argument('--rpc-fault-case',choices=['zero_descriptor_length','unsupported_return_tag','partial_float_eof'],help='One destructive RPC case; candidate immediately restored, never reused')
    p.add_argument('--observer-active',action='store_true',help='Bounded concurrent CoreDMA workload/observer sampling; requires diagnostic observer manifest')
    p.add_argument('--extended',action='store_true',help='Candidate only: three cycles each of full CoreDMA and exception suites')
    p.add_argument('--artiq-python',default=str(BASE/'venvs/artiq-host/bin/python'))
    p.add_argument('--artiq-run',default=str(Path.home()/'.local/bin/artiq_run'))
    a=p.parse_args();manifest=json.loads(a.manifest.read_text());files=preflight(manifest)
    dma_observer=bool(manifest.get('dma_observer'))
    if a.observer_active and (not dma_observer or a.extended):p.error('Active observer requires diagnostic observer manifest and excludes extended suite')
    if dma_observer and (a.trained_observer_manifest or a.ocm_manifest or a.fsbl_spd or a.rpc_fault_case):
        p.error('Diagnostic DMA observer excludes boot/OCM/fault modes')
    if a.trained_observer_manifest and (a.fsbl_spd or a.ocm_manifest or a.extended or a.rpc_fault_case or a.expect_kernel_state):p.error('Trained observer excludes other candidate modes')
    observer=observer_preflight(a.trained_observer_manifest,files) if a.trained_observer_manifest else None
    if a.fsbl_spd and (a.ocm_manifest or a.extended or a.rpc_fault_case or a.expect_kernel_state):p.error('FSBL SPD mode excludes OCM/extended/fault modes')
    if a.fsbl_spd:spd_preflight(json.loads(a.manifest.read_text()),files)
    if a.ocm_manifest and (a.extended or a.rpc_fault_case or a.expect_kernel_state):p.error('OCM mode excludes runtime/fault suites')
    ocm=ocm_preflight(a.ocm_manifest,files) if a.ocm_manifest else None
    if a.expect_kernel_state and not a.rpc_fault_case:p.error('--expect-kernel-state requires --rpc-fault-case')
    out=a.output.resolve()
    if out.exists():raise ValueError('Use a fresh output directory')
    if a.execute and not all((a.server,a.port,a.interface)):p.error('Execution requires --server --port --interface')
    storage=require_runtime_space(out,REPO) if a.execute else None
    out.mkdir(parents=True)
    if not a.execute:
        (out/'results.json').write_text(json.dumps(dict(status='PREFLIGHT_PASS_NO_HARDWARE_ACCESS',hardware_executed=False),indent=2)+'\n')
        print('PREFLIGHT_PASS_NO_HARDWARE_ACCESS');return 0
    # No device opens, network accesses or subprocess hardware operations above.
    with lease() as held:
        # Recheck after obtaining ownership, before touching hardware.
        storage=require_runtime_space(out,REPO)
        preflight(json.loads(a.manifest.read_text()))
        if a.ocm_manifest:ocm_preflight(a.ocm_manifest,files)
        if observer:observer_preflight(a.trained_observer_manifest,files)
        if a.fsbl_spd:spd_preflight(json.loads(a.manifest.read_text()),files)
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
            return text
        def cycle(prefix):
            if prefix=='candidate' and observer is not None:
                run('candidate-trained-observer',[sys.executable,str(REPO/'scripts/run_trained_observer.py'),
                    '--server',a.server,'--port',a.port,'--elf',observer['elf']['path'],
                    '--symbols',observer['symbols']['path'],'--fsbl',files['candidate_fsbl']['path'],
                    '--pmu',files['candidate_pmu']['path'],'--output',str(out/'candidate-trained-observer')]+(['--pmu-boundary-inputs',observer['pmu_boundary_inputs']['path']] if observer.get('pmu_boundary_inputs') else [])+(['--model-inputs',observer['model_inputs']['path']] if observer.get('model_inputs') else [])+(['--no-master-inputs',observer['no_master_inputs']['path']] if observer.get('no_master_inputs') else [])+(['--master-inputs',observer['master_inputs']['path']] if observer.get('master_inputs') else [])+(['--peripheral-inputs',observer['peripheral_inputs']['path']] if observer.get('peripheral_inputs') else [])+(['--definitions-only'] if observer.get('definitions_only') else (['--controls-only'] if observer.get('controls_only') else (['--exception-brk'] if observer.get('exception_brk') else (['--exception-observer'] if observer.get('exception_observer') else [])))),180)
                observed=json.loads((out/'candidate-trained-observer/results.json').read_text())
                if observed.get('status')!='PASS':raise RuntimeError('Trained observer failed')
                if observer.get('exception_brk'):return 'EXPECTED_BRK_CAPTURE_RESTORE_REQUIRED'
                return 'TRAINED_FSBL_OBSERVATION_ONLY' if observer.get('definitions_only') or observer.get('controls_only') else 'TRAINED_OCM_REGISTERS_ONLY'
            if prefix=='candidate' and ocm is not None:
                run('candidate-ocm',[sys.executable,str(REPO/'scripts/run_ocm_environment.py'),
                    '--server',a.server,'--port',a.port,'--elf',ocm['elf']['path'],
                    '--symbols',ocm['symbols']['path'],'--ps-init',ocm['ps_init']['path'],
                    '--output',str(out/'candidate-ocm')],120)
                observed=json.loads((out/'candidate-ocm/results.json').read_text())
                if observed.get('status')!='PASS':raise RuntimeError('OCM observation did not pass')
                return 'OCM_UART_ONLY_NO_NETWORK'
            def path(name):return files[prefix+'_'+name]['path']
            ps=Path(path('fsbl')).parents[2];worker=Path(path('worker')).parent
            load=out/(prefix+'-load')
            run(prefix+'-load',[sys.executable,str(REPO/'scripts/load_rtio_runtime.py'),
                '--server',a.server,'--cable',CABLE,'--port',a.port,'--ps-export',str(ps),
                '--bitstream',path('pl'),'--worker',str(worker),'--cpu0',path('cpu0'),'--output',str(load)],240)
            loaded=json.loads((load/'results.json').read_text())
            if loaded.get('status')!='PASS':raise RuntimeError('Loader did not report PASS')
            def observer_read(phase):
                from dma_observer_candidate import verify_snapshot
                text=run('candidate-observer-'+phase,['vivado-container','shell','-c','exec "$@"','bash',
                    '/srv/codex-hil-data/toolchains/amd/Xilinx/2025.2/Vivado/bin/xsdb',
                    str(REPO/'scripts/probe_dma_observer.tcl'),a.server,CABLE],45)
                decoded=verify_snapshot(text)
                (out/('candidate-observer-'+phase+'.json')).write_text(json.dumps(decoded,indent=2)+'\n')
            if prefix=='candidate' and dma_observer:observer_read('before')
            if prefix=='candidate' and a.fsbl_spd:
                run('candidate-fsbl-spd',[sys.executable,str(REPO/'scripts/decode_fsbl_spd_log.py'),
                    '--log',str(load/'uart.log'),'--output',str(out/'candidate-fsbl-spd')],30)
            ip=loaded['ip'];db=out/(prefix+'-device-db.py')
            text=(REPO/'examples/device_db_genesys.py').read_text()
            text,count=re.subn(r'([\"\']host[\"\']\s*:\s*[\"\'])\d+\.\d+\.\d+\.\d+([\"\'])',lambda m:m[1]+ip+m[2],text)
            if count!=1:raise ValueError('Expected one core address in copied database')
            db.write_text(text)
            if prefix=='candidate' and a.observer_active:
                run('candidate-observer-active',[sys.executable,str(REPO/'scripts/run_dma_observer_active.py'),
                    '--server',a.server,'--device-db',str(db),'--artiq-run',a.artiq_run,
                    '--output',str(out/'candidate-observer-active')],110)
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
                    '--case',a.rpc_fault_case,'--ip',ip,'--device-db',str(db),'--output',str(fault)]+(['--require-kernel-state'] if a.expect_kernel_state else []),90)
                observed=json.loads((fault/'results.json').read_text())
                if observed.get('status')!='FAULT_TERMINATION_OBSERVED_RESTORE_REQUIRED':
                    raise RuntimeError('RPC fault observation incomplete')
                run('candidate-rpc-terminal-event',['vivado-container','shell','-c','exec "$@"','bash',
                    '/srv/codex-hil-data/toolchains/amd/Xilinx/2025.2/Vivado/bin/xsdb',
                    str(REPO/'scripts/probe_rpc_failstop.tcl'),a.server,CABLE],30)
                return ip  # Read-only observation only; no kernel reuse before restoration.
            run(prefix+'-ethernet',[sys.executable,str(REPO/'scripts/test_ethernet_hw.py'),'--ip',ip,'--interface',a.interface,'--output',str(out/(prefix+'-ethernet.json'))],90)
            if prefix=='candidate' and dma_observer:observer_read('after')
            return ip
        # Convert external termination to an exception so restoration is attempted.
        old_handler=signal.signal(signal.SIGTERM,lambda *_:(_ for _ in ()).throw(RuntimeError('Termination requested')))
        try:result=lifecycle(cycle)
        finally:signal.signal(signal.SIGTERM,old_handler)
        result.update(dma_observer=dma_observer,dma_observer_active=a.observer_active,kind='candidate-runtime-hardware',hardware_executed=True,lock=str(LOCK),cable=CABLE,
                      elapsed_seconds=round(time.monotonic()-started,3),stages=stages,extended=a.extended,rpc_fault_case=a.rpc_fault_case,expect_kernel_state=a.expect_kernel_state,ocm_observation=ocm is not None,fsbl_spd=a.fsbl_spd,trained_observer=observer is not None,observer_probe=('brk' if observer.get('exception_brk') else 'normal') if observer else None,observer_manifest_sha256=hashlib.sha256(a.trained_observer_manifest.read_bytes()).hexdigest() if observer else None,
                      manifest_sha256=hashlib.sha256(a.manifest.read_bytes()).hexdigest(),storage_admission=storage)
        (out/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    return 0 if result['status']=='PASS' and result['restoration']=='PASS' else 1

if __name__=='__main__':raise SystemExit(main())
