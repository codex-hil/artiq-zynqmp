"""Active lab stage inside the existing all-board parent; LGPL-3.0-or-later.

No standalone entrypoint. All artifacts/idle proof admitted before programming;
parent owns exclusive UART and all leases, and always restores both boards.
"""
import os,re,runpy,time
from pathlib import Path
from lab_idle_probe import probe as idle_probe,post_fault,failure_snapshot
from lab_fault_process import run as run_child
from active_dma_fault_evidence import validate_logged_metrics
ROOT=Path(__file__).resolve().parents[2]


def probe(session,master_host,uart,raw):
    c=session.config;out=session.output
    if session.lab_fault_mode!='active':raise ValueError('Explicit active laboratory session required')
    # The parent's prepare() already verifies this descriptor's shared lock inode.
    if not hasattr(session,'lease_fd'):raise ValueError('Parent board lease required')
    before=idle_probe(uart,raw)
    begin=len(raw)
    db=runpy.run_path(str(out/'dio-device-db.py'))['device_db']
    db['core_dma']={'type':'local','module':'artiq.coredevice.dma','class':'CoreDMA'}
    path=out/'lab-active-device-db.py';path.write_text('device_db = '+repr(db)+'\n')
    env=os.environ.copy();env['PYTHONPATH']=c['dma_cursor_overlay']
    try:
        log=run_child([c['artiq_python'],'-m','artiq.frontend.artiq_run','--device-db='+str(path),
            '--dataset-db='+str(out/'lab-active-datasets.mdb'),
            str(ROOT/'examples/kasli_drtio_native_dma_active_fault.py')],
            directory=out/'lab-arm-handshake',log=out/'lab-active-kernel.log',uart=uart,raw=raw,
            lease_fd=session.lease_fd,timeout=60,env=env,cwd=ROOT)
    except Exception:
        # Same exclusive UART/leases; preserve original child failure and do not
        # retry playback, arm, reset, clear or erase before outer restoration.
        session.result['lab_active_fault']='FAIL'
        try:
            session.result.update(failure_snapshot(uart,raw))
        except Exception as sample_error:
            session.result['lab_failure_sample_error']=str(sample_error)
        raise
    deadline=time.monotonic()+.1
    while time.monotonic()<deadline:raw.extend(uart.read(uart.in_waiting or 1))
    post=post_fault(uart,raw,before)
    markers=re.findall(r'^NATIVE_DDMA_ACTIVE_UNDERFLOW_CAUGHT_PASS timestamp=(\d+)\r?$',log,re.M)
    if len(markers)!=1:raise RuntimeError('Missing unique caught-underflow timestamp')
    evidence=validate_logged_metrics(bytes(raw[begin:]).decode(errors='replace'),log,expected_timestamp=int(markers[0]))
    if (evidence['accepted'],evidence['completed'])!=(1,1):
        raise RuntimeError('Active telemetry must match pristine one-play post-state counters')
    session.result.update(lab_active_fault='PASS',lab_active_evidence=evidence,
                          lab_active_idle_before=before,**post)
