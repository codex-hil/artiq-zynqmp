#!/usr/bin/env python3
"""Standard ARTIQ CoreDMA API, DDR FPGA playback and physical JB1→JB2 edges."""
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
    result={'kind':'hardware','scope':__doc__,'status':'FAIL','ip':o.ip,'cycles':o.cycles,'runs':[]}
    def counter():
        m=CommMgmt(o.ip)
        try:m.open();return int(m.config_read('rtio_counter'))
        finally:m.close()
    def run(source,marker=None,loopbacks=0,negative=False):
        proc=subprocess.run([str(Path(sys.executable).with_name('artiq_run')),'--device-db',str(db),
                             '--dataset-db',str(out/'datasets.mdb'),str(repo/'examples'/source)],
                            capture_output=True,text=True,timeout=40)
        log=proc.stdout+proc.stderr
        (out/f'run-{len(result["runs"])}-{Path(source).stem}.log').write_text(log)
        result['runs'].append({'source':source,'returncode':proc.returncode,'stdout':proc.stdout,'stderr':proc.stderr})
        if negative:
            if proc.returncode!=1 or not re.search(r'^artiq\.coredevice\.exceptions\.DMAError: DMA trace not found',log,re.M):raise RuntimeError('Missing typed host DMAError')
            if 'Core Device Traceback' not in log or 'KernelStartupFailed' in log:raise RuntimeError('Invalid exception behavior')
            return
        if proc.returncode or (marker and marker not in proc.stdout):raise RuntimeError('CoreDMA fixture failed: '+source)
        matches=re.findall(r'^COREDMA_LOOPBACK_PASS (\d+) (\d+) (\d+) (-?\d+)$',proc.stdout,re.M)
        if len(matches)!=loopbacks:raise RuntimeError('Wrong physical DMA edge validation count')
        for start,first,duration,extra in matches:
            if int(first)-int(start)!=1250015 or int(duration)!=1350000 or int(extra)!=-1:raise RuntimeError('Incorrect physical DMA timing')
    try:
        before=counter();result['counter_before']=before
        for _ in range(o.cycles):
            run('genesys_dma.py',loopbacks=2)
            run('genesys_dma_errors.py','COREDMA_ERRORS_PASS')
            run('genesys_dma_persistence.py','COREDMA_PERSISTENCE_PASS',loopbacks=2)
            run('genesys_dma_store_limits.py','COREDMA_LIMITS_PASS')
            run('genesys_dma_missing.py',negative=True)
            # Actual successful record/load/playback immediately after uncaught error.
            run('genesys_dma.py',loopbacks=2)
        after=counter()
        if after<=before:raise RuntimeError('RTIO counter stopped/reset')
        result.update(status='PASS',counter_after=after,validated_pulses=o.cycles*24,
                      validated_edges=o.cycles*48,width_mu=12500,input_latency_mu=15,
                      record_slot_limit=32,slot_bytes=65536,name_bytes_limit=64)
    except Exception as error:result['failure']=str(error)
    (out/'results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
    return 0 if result['status']=='PASS' else 1

if __name__=='__main__':raise SystemExit(main())
