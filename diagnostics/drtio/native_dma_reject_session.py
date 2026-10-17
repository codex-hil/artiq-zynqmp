"""Expected native upload failure, then normal playback; LGPL-3.0-or-later."""
import os,re,subprocess,time
from pathlib import Path


def rejection_result(returncode,host_log,aux_log,master_log):
    if returncode<=0 or 'NATIVE_DDMA_OVERSIZE_UNEXPECTED_ACCEPT' in host_log:
        raise RuntimeError('Oversize kernel unexpectedly succeeded or was killed')
    if 'error adding DMA trace on satellite #0' not in master_log:
        raise RuntimeError('Missing concrete upstream upload rejection')
    rows=re.findall(r'AUX_DDMA UPLOAD id=(\d+) status=(\d+) bytes=(\d+)',aux_log)
    if (len(rows)!=2 or [tuple(map(int,row[1:])) for row in rows]!=[(1,1010),(2,44)] or rows[0][0]!=rows[1][0]):
        raise RuntimeError('Wrong rejected upload fragments/identity')
    ident=rows[0][0]
    replies=re.findall(r'AUX_DDMA REPLY kind=(\d+) id=(\d+) succeeded=(\d+)',aux_log)
    if replies!=[('177',ident,'1'),('177',ident,'0')] or 'AUX_DDMA STATUS' in aux_log:
        raise RuntimeError('Expected only first ACK and final NACK, no playback/status')
    if any(t in aux_log for t in ('AUX_DDMA FAIL_CLOSED','AUX_FW PANIC','AUX_SERVICE SEND_FAIL','AUX_SERVICE RX_ERROR')):
        raise RuntimeError('Satellite fault cannot count as upload rejection')
    return dict(native_ddma_rejection='PASS',native_ddma_rejected_bytes=1054,
        native_ddma_rejection_fragments=[1010,44],native_ddma_rejected_trace_id=int(ident),
        native_ddma_rejection_scope='native upload ACK/NACK and concrete master error; no playback request; subsequent normal playback must pass separately')


def attempt(session,master_host,uart,raw,device_db):
    c=session.config;out=session.output;begin=len(raw)
    env=os.environ.copy();env.pop('PYTHONPATH',None)
    env['GENESYS_LEASE_FD']=str(session.lease_fd)
    example=Path(__file__).resolve().parents[2]/'examples/kasli_drtio_native_dma_oversize.py'
    # Parent retains every board lease through both this expected failure and
    # the following positive recovery experiment. Timeout always fails the test.
    process=subprocess.run([c['artiq_python'],'-m','artiq.frontend.artiq_run',
        '--device-db='+str(device_db),'--dataset-db='+str(out/'reject-datasets.mdb'),str(example)],
        cwd=Path(__file__).resolve().parents[2],env=env,capture_output=True,text=True,
        timeout=30,pass_fds=(session.lease_fd,))
    host_log=process.stdout+process.stderr
    (out/'master-native-ddma-rejection.log').write_text(host_log)
    end=time.monotonic()+1
    while time.monotonic()<end:raw.extend(uart.read(uart.in_waiting or 1))
    master=session.run('master-after-native-rejection-log',[c['artiq_python'],'-m',
        'artiq.frontend.artiq_coremgmt','-D',master_host,'log'],timeout=15,host=True)
    result=rejection_result(process.returncode,host_log,raw[begin:].decode(errors='replace'),master)
    if c.get('native_ddma_structured_error'):
        from structured_dma_evidence import structured_rejection_result
        result.update(structured_rejection_result(host_log,master,''))
    return result
