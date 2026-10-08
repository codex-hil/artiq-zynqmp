#!/usr/bin/env python3
"""Catch/propagate/recover real Genesys kernels, without JTAG resets during tests."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
import time
from artiq.coredevice.comm_mgmt import CommMgmt


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--ip',required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--cycles',type=int,default=3)
    o=p.parse_args()
    if o.cycles<1:p.error('--cycles must be positive')
    repo=Path(__file__).resolve().parent.parent
    out=o.output.resolve();out.mkdir(parents=True,exist_ok=True)
    db=out/'device_db.py';db.write_text((repo/'examples/device_db_genesys.py').read_text().replace('192.168.2.16',o.ip))
    result={'kind':'hardware','time':time.time(),'ip':o.ip,'tests':{},'runs':[],
            'scope':'native catch/reraise/finally, kernel/RPC/RTIO exceptions, worker recovery with CPU0/PL preserved'}
    def counter():
        m=CommMgmt(o.ip)
        try:
            m.open()
            if m.config_read('runtime_mode')!=b'kernel-bringup':raise RuntimeError('Wrong runtime')
            return int(m.config_read('rtio_counter'))
        finally:m.close()
    def run(name,marker=None,error=None):
        proc=subprocess.run([str(Path(sys.executable).with_name('artiq_run')),'--device-db',str(db),
                '--dataset-db',str(out/'datasets.mdb'),str(repo/'examples'/name)],
                capture_output=True,text=True,timeout=35)
        text=proc.stdout+proc.stderr
        index=len(result['runs']);(out/f'run-{index}-{Path(name).stem}.log').write_text(text)
        result['runs'].append({'source':name,'returncode':proc.returncode,'stdout':proc.stdout,'stderr':proc.stderr})
        if error:
            if proc.returncode!=1 or not re.search(error,text,re.M):raise RuntimeError('Expected typed exception missing: '+name)
            if 'KernelStartupFailed' in text or 'ConnectionResetError' in text:raise RuntimeError('Worker failed instead of reporting exception')
        elif proc.returncode or marker not in proc.stdout:raise RuntimeError('Kernel did not continue: '+name)
    try:
        before=counter();result['counter_before']=before
        for cycle in range(o.cycles):
            run('genesys_exceptions.py','EXCEPTION_CATCH_PASS')
            run('genesys_nested_exceptions.py','NESTED_EXCEPTION_PASS')
            run('genesys_rtio_overflow.py','RTIO_OVERFLOW_PASS')
            run('genesys_exception_same_connection.py','SAME_CONNECTION_RECOVERY_PASS')
            for source,error in [('genesys_rtio_underflow.py',r'^artiq\.coredevice\.exceptions\.RTIOUnderflow:'),
                                 ('genesys_uncaught_exception.py',r'^ValueError: intentional uncaught kernel failure'),
                                 ('genesys_uncaught_rpc.py',r'^ValueError: intentional uncaught RPC failure')]:
                run(source,error=error)
                # Fresh actual kernel compile/load/RPC immediately after every error.
                run('genesys_network_probe.py','NETWORK_KERNEL_RETURN_PASS 3.75')
                current=counter()
                if current<=before:raise RuntimeError('RTIO time stopped or reset across error recovery')
                before=current
            result['tests'][f'cycle_{cycle}_catch_and_recovery']='PASS'
        result['counter_after']=counter()
        m=CommMgmt(o.ip)
        try:m.open();result['runtime_log']=m.get_log()
        finally:m.close()
        if 'worker recovered after kernel exception.' not in result['runtime_log']:raise RuntimeError('No recovery event')
        result['status']='PASS'
    except Exception as error:
        result.update(status='FAIL',failure=str(error))
    (out/'results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
    return 0 if result['status']=='PASS' else 1

if __name__=='__main__':raise SystemExit(main())
