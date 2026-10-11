#!/usr/bin/env python3
"""Bounded AUX diagnostic plus guaranteed attempt to restore normal core.

LGPL-3.0-or-later. Shared exact-board lock covers reset/load/test/restore.
"""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

REPO=Path(__file__).resolve().parent.parent
CABLE='210383B7F02DA'
LOCK=Path.home()/'.cache'/('genesys-'+CABLE+'.lock')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('server','port','ps-export','bitstream','csr-map','restore-bitstream',
                 'worker','cpu0','device-db','artiq-python','artiq-run','output'):
        p.add_argument('--'+name,required=True)
    p.add_argument('--firmware',help='Optional built AUX firmware ELF')
    a=p.parse_args()
    out=Path(a.output).resolve();out.mkdir(parents=True,exist_ok=True)
    bit=Path(a.bitstream).resolve()
    build=json.loads((bit.parent/'results.json').read_text())
    if build.get('status')!='PASS':p.error('AUX FPGA build must pass verification')
    mapping=json.loads(Path(a.csr_map).read_text())
    if 'aux_bridge_busy' not in mapping.get('registers',{}):p.error('AUX CSR map required')
    # Reject stale/mismatched maps and bitstream before any board action.
    for file,key in ((bit,'top.bit'),(Path(a.csr_map),'csr-map.json')):
        digest=hashlib.sha256(file.read_bytes()).hexdigest()
        if build['sha256'].get(key)!=digest:p.error('Build artifact hash mismatch: '+str(file))
    for file in (a.restore_bitstream,a.cpu0,a.device_db,
                 str(Path(a.worker)/'worker32.elf'),str(Path(a.worker)/'start64.elf')):
        if not Path(file).is_file():p.error('Missing restoration input: '+file)
    LOCK.parent.mkdir(parents=True,exist_ok=True)
    lease=LOCK.open('a')
    try:fcntl.flock(lease,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError:p.error('Genesys is busy; shared board lock held elsewhere')
    started=time.time()
    result={'kind':'hardware-bringup','status':'FAIL','restoration':'NOT_RUN',
            'cable':CABLE,'lock':str(LOCK),'started':started,'stages':{}}
    def run(stage,command,timeout=300,env=None):
        print(stage+' START',flush=True)
        childenv=(env or os.environ).copy()
        childenv['GENESYS_LEASE_FD']=str(lease.fileno())
        r=subprocess.run(command,cwd=REPO,capture_output=True,text=True,
                         timeout=timeout,env=childenv,pass_fds=(lease.fileno(),))
        log=r.stdout+r.stderr;(out/(stage+'.log')).write_text(log)
        result['stages'][stage]={'exit_code':r.returncode,
                               'log_sha256':hashlib.sha256(log.encode()).hexdigest()}
        if r.returncode:raise RuntimeError(stage+' failed: '+log[-2000:])
        print(stage+' PASS',flush=True)
    common=['--server',a.server,'--cable',CABLE,'--port',a.port,'--ps-export',a.ps_export]
    touched=False
    try:
        touched=True
        run('diagnostic-load',[sys.executable,str(REPO/'scripts/load_drtio_diagnostic.py'),
            *common,'--bitstream',str(bit),'--output',str(out/'diagnostic-load')])
        run('phy',[sys.executable,str(REPO/'diagnostics/drtio/test_phy_hw.py'),
            '--server',a.server,'--cable',CABLE,'--csr-map',a.csr_map,
            '--output',str(out/'phy')],timeout=120)
        run('aux',[sys.executable,str(REPO/'diagnostics/drtio/test_aux_hw.py'),
            '--server',a.server,'--cable',CABLE,'--csr-map',a.csr_map,
            '--output',str(out/'aux')],timeout=360)
        if a.firmware:
            run('aux-firmware',[sys.executable,str(REPO/'diagnostics/drtio/aux_protocol/test_firmware_hw.py'),
                '--server',a.server,'--port',a.port,'--elf',a.firmware,
                '--csr-map',a.csr_map,'--output',str(out/'aux-firmware')],timeout=120)
        result['status']='PASS' 
    except Exception as e:
        result['error']=str(e);print('Diagnostic FAIL: '+str(e),flush=True)
    finally:
        if touched:
            try:
                run('restore-load',[sys.executable,str(REPO/'scripts/load_rtio_runtime.py'),
                    *common,'--bitstream',a.restore_bitstream,'--worker',a.worker,
                    '--cpu0',a.cpu0,'--output',str(out/'restore-load')])
                ip=json.loads((out/'restore-load/results.json').read_text())['ip']
                result['restored_ip']=ip
                text=Path(a.device_db).read_text()
                text,n=re.subn(r'([\"\']host[\"\']\s*:\s*[\"\'])\d+\.\d+\.\d+\.\d+([\"\'])',
                               lambda m:m[1]+ip+m[2],text)
                if not n:raise RuntimeError('Cannot update core host in copied device database')
                db=out/'device_db.py';db.write_text(text)
                hostenv=os.environ.copy();hostenv.pop('PYTHONPATH',None)
                run('restored-debug',[a.artiq_python,str(REPO/'scripts/test_rtio_debug_hw.py'),
                    '--ip',ip,'--device-db',str(db),'--artiq-run',a.artiq_run,
                    '--output',str(out/'restored-debug')],timeout=240,env=hostenv)
                run('restored-ethernet',[sys.executable,str(REPO/'scripts/test_ethernet_hw.py'),
                    '--ip',ip,'--output',str(out/'restored-ethernet.json')],timeout=90)
                result['restoration']='PASS'
            except Exception as e:
                result['status']='FAIL';result['restoration']='FAIL'
                result['restoration_error']=str(e);print('Restore FAIL: '+str(e),flush=True)
        result['elapsed_seconds']=round(time.time()-started,3)
        (out/'results.json').write_text(json.dumps(result,indent=2)+'\n')
        lease.close()
    print(json.dumps(result,indent=2))
    return 0 if result['status']=='PASS' and result['restoration']=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
