#!/usr/bin/env python3
"""FSBL-trained observer child; inherited lease/restoration required. LGPL-3.0-or-later."""
import argparse
import json
import re
import subprocess
import time
from pathlib import Path
from inject_rpc_fault import require_lease
from check_hw_storage import require_runtime_space
from check_el3_observer import check
from check_fsbl_observer_entry import descriptor

REPO = Path(__file__).resolve().parents[1]
XSDB = '/srv/codex-hil-data/toolchains/amd/Xilinx/2025.2/Vivado/bin/xsdb'


def decode(text):
    pairs = re.findall(r'^OBSERVER_REGISTER (x\d+) (\d+)$', text, re.M)
    expected = {'x'+str(i) for i in range(10)} | {'x15'}
    if len(pairs) != 11 or {k for k,v in pairs} != expected:
        raise ValueError('Missing/duplicate observer registers')
    regs = {k:int(v) for k,v in pairs}
    if regs['x0'] != 12 or regs['x15'] != 0x33 or regs['x9'] != 0xfffc0000:
        raise ValueError('Observer marker/EL/entry mismatch')
    if regs['x1'] & 0x1005 or regs['x6'] & 0x3c0 != 0x3c0 or regs['x7'] & 255:
        raise ValueError('Observed entry controls changed')
    if re.findall(r'^OBSERVER_PC (\d+)$', text, re.M) != [str(0xfffc0034)]:
        raise ValueError('Missing/wrong observer terminal')
    return regs


def decode_exception(text):
    names={'x'+str(i) for i in range(10)}|{'x'+str(i) for i in range(14,22)}
    pairs=re.findall(r'^EXCEPTION_REGISTER (x\d+) (\d+)$',text,re.M)
    if len(pairs)!=len(names) or {k for k,v in pairs}!=names:
        raise ValueError('Incomplete/duplicate exception-observer registers')
    regs={k:int(v) for k,v in pairs}
    if (regs['x0'],regs['x9'],regs['x15'])!=(12,0xfffc8800,0x33):
        raise ValueError('Fault/wrong EL/entry marker; never normal PASS')
    if regs['x1']&0x1005 or regs['x6']&0x2c0!=0x2c0 or regs['x7']&255:
        raise ValueError('Unexpected observed controls')
    markers={'EXCEPTION_ARMED_VBAR':0xfffc8000,'EXCEPTION_STOP_PC':0xfffc8834}
    for name,value in markers.items():
        if re.findall(r'^'+name+r' (\d+)$',text,re.M)!=[str(value)]:
            raise ValueError('Missing/duplicate/wrong '+name)
    if text.splitlines().count('EXCEPTION_OBSERVER_NORMAL_COMPLETE')!=1:
        raise ValueError('Normal completion missing or duplicated')
    return regs


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('server','port','elf','fsbl','pmu','symbols','output'):
        p.add_argument('--'+name, required=True)
    p.add_argument('--peripheral-inputs',type=Path)
    p.add_argument('--master-inputs',type=Path)
    p.add_argument('--no-master-inputs',type=Path)
    p.add_argument('--model-inputs',type=Path)
    p.add_argument('--pmu-boundary-inputs',type=Path)
    p.add_argument('--pmu-request-inputs',type=Path)
    p.add_argument('--pmu-guard-inputs',type=Path)
    group=p.add_mutually_exclusive_group()
    group.add_argument('--definitions-only',action='store_true')
    group.add_argument('--controls-only',action='store_true')
    group.add_argument('--exception-observer',action='store_true')
    group.add_argument('--exception-brk',action='store_true')
    p.add_argument('--aib-observation',action='store_true',help='Eight fixed read-only AIB reads after guard')
    a=p.parse_args(); require_lease()
    if a.exception_observer or a.exception_brk:
        from check_el3_exception_observer import check as image_check
    else: image_check=check
    image_check(Path(a.elf).read_bytes())
    if a.peripheral_inputs:
        if not a.exception_observer or a.exception_brk:raise ValueError('Require normal exception observer')
        from capture_peripheral_dma_state import preflight as peripheral_preflight, parse as peripheral_parse
        peripheral_preflight(a.peripheral_inputs)
    if a.master_inputs:
        if not a.peripheral_inputs:raise ValueError('Master window requires peripheral window')
        from collect_boot_masters import preflight as master_preflight, collect as collect_masters
        master_preflight(a.master_inputs)
    no_master=None
    if a.no_master_inputs:
        if not a.exception_observer or not a.master_inputs:raise ValueError('Require complete normal observer')
        from no_master_candidate import preflight as no_master_preflight
        no_master=no_master_preflight(a.no_master_inputs,REPO)
    model=None
    if a.model_inputs:
        if not no_master:raise ValueError('Model requires qualified no-master window')
        from check_ddr_ocm_model import preflight as model_preflight, parse as model_parse
        model=model_preflight(a.model_inputs,REPO)
    pmu_diagnostic=None
    if a.pmu_boundary_inputs:
        if not no_master or model:raise ValueError('PMU diagnostic requires no-master window without model')
        from pmu_boundary_candidate import preflight as pmu_preflight, parse as pmu_parse
        pmu_diagnostic=pmu_preflight(a.pmu_boundary_inputs,REPO)
    request=None
    if a.pmu_request_inputs:
        if not no_master or model or pmu_diagnostic:raise ValueError('Request requires separate no-master window')
        from pmu_request_candidate import preflight as request_preflight, parse as request_parse
        request=request_preflight(a.pmu_request_inputs,REPO)
    guard=None
    if a.pmu_guard_inputs:
        if not no_master or model or pmu_diagnostic or request:raise ValueError('Guard requires separate no-master window')
        from pmu_guard_candidate import preflight as guard_preflight, parse as guard_parse
        guard=guard_preflight(a.pmu_guard_inputs,REPO)
    if a.aib_observation and not guard:raise ValueError('AIB observation requires guarded window')
    desc=descriptor(Path(a.fsbl).read_bytes(),Path(a.symbols).read_text())
    out=Path(a.output)
    if out.exists(): raise ValueError('Use fresh output')
    require_runtime_space(out,REPO);out.mkdir(parents=True)
    raw=bytearray();result=dict(status='FAIL',hardware_executed=True,ddr_test='NOT_RUN')
    def xs(name,script,*args):
        command=['vivado-container','shell','-c','exec "$@"','bash',XSDB,str(REPO/'scripts'/script),*map(str,args)]
        r=subprocess.run(command,capture_output=True,text=True,timeout=60)
        (out/(name+'.log')).write_text(r.stdout+r.stderr)
        if r.returncode: raise RuntimeError(name+' failed')
        return r.stdout
    import serial
    try:
        with serial.Serial(a.port,115200,timeout=.2) as uart:
            uart.reset_input_buffer()
            xs('reset','reset_genesys_ps.tcl',a.server,'210383B7F02DA')
            if pmu_diagnostic:pmu_preflight(a.pmu_boundary_inputs,REPO)
            if request:request_preflight(a.pmu_request_inputs,REPO)
            if guard:guard_preflight(a.pmu_guard_inputs,REPO)
            selected_pmu=guard['elf']['path'] if guard else (request['elf']['path'] if request else (pmu_diagnostic['elf']['path'] if pmu_diagnostic else a.pmu))
            xs('boot','run_boot_firmware.tcl',a.server,selected_pmu,a.fsbl,'210383B7F02DA')
            deadline=time.monotonic()+30
            while time.monotonic()<deadline:
                raw.extend(uart.read(uart.in_waiting or 1))
                if b'Exit from FSBL' in raw: break
            else: raise RuntimeError('FSBL UART completion timeout')
            text=xs('observer','run_trained_observer.tcl',a.server,a.elf,desc['terminal_pcs'][0],'210383B7F02DA','definitions' if a.definitions_only else ('controls' if a.controls_only else ('exception-brk' if a.exception_brk else ('exception' if a.exception_observer else 'observe'))))
            if a.definitions_only:
                if text.count('FSBL_REGISTER_DEFINITIONS_BEGIN')!=1 or text.count('FSBL_REGISTER_DEFINITIONS_END')!=1 or text.count('FSBL_SYS_DEFINITIONS_BEGIN')!=1 or text.count('FSBL_SYS_DEFINITIONS_END')!=1 or len(re.findall(r'^FSBL_CPSR_RAW [0-9]+$',text,re.M))!=1:
                    raise ValueError('Incomplete FSBL definitions')
                if re.findall(r'^FSBL_SYS_CHILD_END (\d+)$',text,re.M)!=[str(i) for i in range(16)]:
                    raise ValueError('Incomplete system-register child definitions')
                result.update(status='PASS',scope='FSBL_BACKEND_DEFINITIONS_ONLY_NO_OBSERVER_EXECUTION',fsbl_descriptor=desc)
            elif a.controls_only:
                if text.count('FSBL_CONTROL_STATE ')!=2 or text.count('FSBL_CONTROL_OBSERVATION_ONLY')!=1:
                    raise ValueError('Incomplete control observation')
                result.update(status='PASS',scope='CONTROL_OBSERVATION_ONLY_NO_EXECUTION_ADMISSION',fsbl_descriptor=desc)
            elif a.exception_brk:
                from verify_el3_brk_capture import verify
                result.update(status='PASS',fault_test=verify(text),scope='DELIBERATE_BRK_CAPTURE_REQUIRES_RESTORATION',fsbl_descriptor=desc)
            elif a.exception_observer: result.update(status='PASS',registers=decode_exception(text),scope='EXCEPTION_AWARE_EL3_OBSERVER_NO_DDR_TEST',fsbl_descriptor=desc)
            else: result.update(status='PASS',registers=decode(text),fsbl_descriptor=desc)
            if no_master:
                # CPU0 is already positively stopped at the OCM observer terminal.
                # No normal RTIO preparation: this image has no CSR window.
                no_master_preflight(a.no_master_inputs,REPO)
                command=['vivado','-mode','batch','-source',str(REPO/'scripts/program_genesys_pl.tcl'),'-tclargs',a.server.removeprefix('tcp:'),'210383B7F02DA',no_master['bitstream']['path']]
                r=subprocess.run(command,capture_output=True,text=True,timeout=60)
                (out/'no-master-pl.log').write_text(r.stdout+r.stderr)
                if r.returncode:raise RuntimeError('No-master PL load failed')
                result['no_master_pl_loaded']=True
                result['no_master_bitstream_sha256']=no_master['bitstream']['sha256']
            if a.peripheral_inputs:
                peripheral_preflight(a.peripheral_inputs)
                snapshot=xs('peripheral-window','probe_peripheral_dma_state.tcl',a.server,'210383B7F02DA')
                fields=peripheral_parse(snapshot)
                from check_boot_peripheral_window import check
                result['peripheral_window']=check(fields)
                if not result['peripheral_window']['necessary_fields_pass']:
                    raise ValueError('Boot-window peripheral fields not quiet; restore without DDR writes')
            if a.master_inputs:
                result['master_window']=collect_masters(a.master_inputs,xs,a.server)
                if no_master:
                    from no_master_candidate import verify_configuration
                    result['no_master_configuration']=verify_configuration(result['master_window'])
                if not result['master_window']['necessary_dma_fields_pass']:
                    raise ValueError('Master DMA fields not quiet; restore without DDR writes')
            if pmu_diagnostic:
                result['pmu_diagnostic_sha256']=pmu_diagnostic['elf']['sha256']
                result['pmu_boundary']=pmu_parse(xs('pmu-boundary','probe_pmu_boundary.tcl',a.server,'210383B7F02DA'))
            if request:
                import secrets
                nonce=secrets.randbits(64) or 1
                request_preflight(a.pmu_request_inputs,REPO)
                result['pmu_request_sha256']=request['elf']['sha256']
                result['pmu_request_nonce']=hex(nonce)
                result['pmu_request']=request_parse(xs('pmu-request','probe_pmu_observe_request.tcl',a.server,'210383B7F02DA',nonce&0xffffffff,nonce>>32),nonce)
            if guard:
                import secrets
                nonce=secrets.randbits(64) or 1
                guard_preflight(a.pmu_guard_inputs,REPO)
                result['pmu_guard_sha256']=guard['elf']['sha256']
                result['pmu_guard_nonce']=hex(nonce)
                result['pmu_guard_request_attempted']=True
                result['pmu_guard']=guard_parse(xs('pmu-guard','probe_pmu_lab_guard.tcl',a.server,'210383B7F02DA',nonce&0xffffffff,nonce>>32,guard.get('profile','sleep')),nonce,guard.get('profile','sleep'))
            if a.aib_observation:
                from decode_aib_state import parse as aib_parse
                result['aib_after_guard']=aib_parse(xs('aib-after-guard','probe_aib_state.tcl',a.server,'210383B7F02DA'))
                result['aib_observation_hardware_executed']=True
            if model:
                model_preflight(a.model_inputs,REPO)
                captured=xs('ocm-model','run_ddr_ocm_model.tcl',a.server,model['elf']['path'],'210383B7F02DA')
                result['ocm_model']=model_parse(captured,model.get('mode','normal'))
    except Exception as error: result.update(status='FAIL',error=str(error))
    finally:
        (out/'uart.log').write_bytes(raw)
        (out/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    return 0 if result['status']=='PASS' else 1


if __name__=='__main__': raise SystemExit(main())
