#!/usr/bin/env python3
"""Bounded concurrent workload/sampling child; inherited lease required. LGPL-3.0-or-later."""
import argparse,json,os,signal,subprocess,sys,time
from pathlib import Path
from inject_rpc_fault import require_lease
from test_candidate_runtime_hw import bounded,REPO
from check_dma_observer_active import parse


def validate_workload(text):
    rows=[line for line in text.splitlines() if line.startswith('DMA_OBSERVER_LOAD')]
    if rows!=['DMA_OBSERVER_LOAD 1','DMA_OBSERVER_LOAD 2']:
        raise ValueError('Missing/duplicate/reordered workload phases')


def run_workload(command,log,sampler,ready_timeout=20,total_timeout=90):
    start=time.monotonic();proc=None
    try:
        with log.open('w') as output:
            proc=subprocess.Popen(command,stdout=output,stderr=subprocess.STDOUT,start_new_session=True)
            while True:
                text=log.read_text()
                if 'DMA_OBSERVER_LOAD 1\n' in text:
                    if proc.poll() is not None or 'DMA_OBSERVER_LOAD 2\n' in text:
                        raise ValueError('Workload completed before sampling')
                    break
                if proc.poll() is not None:raise ValueError('Workload exited without start')
                if time.monotonic()-start>ready_timeout:raise TimeoutError('Workload start timeout')
                time.sleep(.05)
            sample_start=time.monotonic()-start
            decoded=sampler()
            sample_end=time.monotonic()-start
            fully_overlapped=proc.poll() is None and 'DMA_OBSERVER_LOAD 2\n' not in log.read_text()
            remaining=total_timeout-(time.monotonic()-start)
            if remaining<=0:raise TimeoutError('Workload total timeout')
            if proc.wait(timeout=remaining)!=0:raise ValueError('Workload failed')
            validate_workload(log.read_text())
            return dict(status='WORKLOAD_AND_SAMPLING_COMPLETE',sampling=decoded,
                        sample_start_seconds=sample_start,sample_end_seconds=sample_end,
                        workload_active_through_sample_end=fully_overlapped,
                        elapsed_seconds=time.monotonic()-start,destructive_test_allowed=False)
    finally:
        if proc is not None:
            # Always terminate the full workload group before restoration, including
            # any descendants even if the direct parent has already exited.
            try:os.killpg(proc.pid,signal.SIGTERM)
            except ProcessLookupError:pass
            try:proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                try:os.killpg(proc.pid,signal.SIGKILL)
                except ProcessLookupError:pass
                proc.wait()
            try:os.killpg(proc.pid,signal.SIGKILL)
            except ProcessLookupError:pass


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ['server','device-db','artiq-run','output']:p.add_argument('--'+n,required=True)
    a=p.parse_args();fd=require_lease();out=Path(a.output)
    if out.exists():raise ValueError('Use fresh output')
    out.mkdir(parents=True);result=dict(status='FAIL',hardware_executed=True)
    previous=signal.signal(signal.SIGTERM,lambda *_:(_ for _ in ()).throw(RuntimeError('Termination requested')))
    try:
        def sampler():
            cmd=['vivado-container','shell','-c','exec "$@"','bash',
                 '/srv/codex-hil-data/toolchains/amd/Xilinx/2025.2/Vivado/bin/xsdb',
                 str(REPO/'scripts/probe_dma_observer_active.tcl'),a.server,'210383B7F02DA']
            try:code,text=bounded(cmd,45,os.environ.copy(),fd)
            except subprocess.TimeoutExpired as error:
                text=error.output or '';text=text.decode(errors='replace') if isinstance(text,bytes) else text
                (out/'sampling.log').write_text(text);raise
            (out/'sampling.log').write_text(text)
            if code:raise RuntimeError('Active sampler failed')
            return parse(text)
        command=[a.artiq_run,'--device-db',a.device_db,'--dataset-db',str(out/'datasets.mdb'),str(REPO/'examples/genesys_dma_observer_load.py')]
        result.update(run_workload(command,out/'workload.log',sampler))
    except Exception as error:result.update(status='FAIL',error=str(error))
    finally:
        signal.signal(signal.SIGTERM,previous)
        (out/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    return 0 if result['status']=='WORKLOAD_AND_SAMPLING_COMPLETE' else 1

if __name__=='__main__':raise SystemExit(main())
