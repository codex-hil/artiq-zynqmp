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


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('server','port','elf','fsbl','pmu','symbols','output'):
        p.add_argument('--'+name, required=True)
    p.add_argument('--definitions-only',action='store_true')
    a=p.parse_args(); require_lease()
    check(Path(a.elf).read_bytes())
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
            xs('boot','run_boot_firmware.tcl',a.server,a.pmu,a.fsbl,'210383B7F02DA')
            deadline=time.monotonic()+30
            while time.monotonic()<deadline:
                raw.extend(uart.read(uart.in_waiting or 1))
                if b'Exit from FSBL' in raw: break
            else: raise RuntimeError('FSBL UART completion timeout')
            text=xs('observer','run_trained_observer.tcl',a.server,a.elf,desc['terminal_pcs'][0],'210383B7F02DA','definitions' if a.definitions_only else 'observe')
            if a.definitions_only:
                if text.count('FSBL_REGISTER_DEFINITIONS_BEGIN')!=1 or text.count('FSBL_REGISTER_DEFINITIONS_END')!=1 or text.count('FSBL_SYS_DEFINITIONS_BEGIN')!=1 or text.count('FSBL_SYS_DEFINITIONS_END')!=1 or len(re.findall(r'^FSBL_CPSR_RAW [0-9]+$',text,re.M))!=1:
                    raise ValueError('Incomplete FSBL definitions')
                if re.findall(r'^FSBL_SYS_CHILD_END (\d+)$',text,re.M)!=[str(i) for i in range(16)]:
                    raise ValueError('Incomplete system-register child definitions')
                result.update(status='PASS',scope='FSBL_BACKEND_DEFINITIONS_ONLY_NO_OBSERVER_EXECUTION',fsbl_descriptor=desc)
            else: result.update(status='PASS',registers=decode(text),fsbl_descriptor=desc)
    except Exception as error: result['error']=str(error)
    finally:
        (out/'uart.log').write_bytes(raw)
        (out/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    return 0 if result['status']=='PASS' else 1


if __name__=='__main__': raise SystemExit(main())
