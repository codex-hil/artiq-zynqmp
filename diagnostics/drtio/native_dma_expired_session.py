"""Same-kernel expired playback admission/recovery; LGPL-3.0-or-later."""
import re,runpy,time
from pathlib import Path


def expired_result(log,aux,master):
    marker='NATIVE_DDMA_EXPIRED_START_CAUGHT_PASS'
    physical=re.search(r'NATIVE_DDMA_PHYSICAL_PASS edges=8 width_mu=8000 period_mu=80000 first_delta_mu=(\d+)',log)
    if (log.count(marker)!=1 or not physical or log.index(marker)>physical.start() or
            not 1000000<=int(physical[1])<1100000):
        raise RuntimeError('Missing caught expired-start error followed by physical recovery')
    if ('DDMA playback rejected:' not in master or 'error playing back DMA trace' not in master or
            any(t in master for t in ('session aborted:','Error erasing trace on DMA')) or
            any(t in log for t in ('ConnectionResetError','Previous kernel did not cleanly finish'))):
        raise RuntimeError('Playback rejection must be concrete and recover cleanly')
    uploads=re.findall(r'AUX_DDMA UPLOAD id=(\d+) status=(\d+) bytes=(\d+)',aux)
    if len(uploads)!=1 or uploads[0][1:]!=('3','170'):
        raise RuntimeError('Expected one valid170-byte trace')
    ident=uploads[0][0];events=[]
    for line in aux.splitlines():
        m=re.fullmatch(r'AUX_DDMA REPLY kind=(\d+) id=(\d+) succeeded=(\d+)',line)
        if m:events.append((int(m[1]),m[2],int(m[3])))
        m=re.fullmatch(r'AUX_DDMA STATUS id=(\d+) error=(\d+)',line)
        if m:events.append((182,m[1],1 if int(m[2])==0 else 0))
    expected=[(177,ident,1),(181,ident,0),(181,ident,1),(182,ident,1),(179,ident,1)]
    if events!=expected:raise RuntimeError('Expected upload ACK, expired start NACK, future start/status/erase ACK')
    if any(t in aux for t in ('AUX_DDMA FAIL_CLOSED','AUX_FW PANIC','AUX_SERVICE SEND_FAIL','AUX_SERVICE RX_ERROR')):
        raise RuntimeError('Firmware fault during playback admission recovery')
    return dict(native_ddma_expired_start='PASS',native_ddma='PASS',native_ddma_edges=8,
        native_ddma_id=int(ident),native_ddma_first_delta_mu=int(physical[1]),
        native_ddma_expired_scope='valid trace, start timestamp8 NACK and caught DMAError, future playback in same kernel without reset/reupload; not a hardware playback fault')


def probe(session,master_host,uart,raw):
    c=session.config;out=session.output;begin=len(raw)
    db=runpy.run_path(str(out/'dio-device-db.py'))['device_db']
    db['core_dma']={'type':'local','module':'artiq.coredevice.dma','class':'CoreDMA'}
    path=out/'expired-device-db.py';path.write_text('device_db = '+repr(db)+'\n')
    before=session.run('master-before-expired-log',[c['artiq_python'],'-m','artiq.frontend.artiq_coremgmt','-D',master_host,'log'],timeout=15,host=True)
    log=session.run('master-native-expired-probe',[c['artiq_python'],'-m','artiq.frontend.artiq_run',
        '--device-db='+str(path),'--dataset-db='+str(out/'expired-datasets.mdb'),
        str(Path(__file__).resolve().parents[2]/'examples/kasli_drtio_native_dma_expired.py')],timeout=60,host=True)
    end=time.monotonic()+1
    while time.monotonic()<end:raw.extend(uart.read(uart.in_waiting or 1))
    after=session.run('master-after-expired-log',[c['artiq_python'],'-m','artiq.frontend.artiq_coremgmt','-D',master_host,'log'],timeout=15,host=True)
    bad=r'reset failed|RTIO (?:sequence|collision|busy) error|failed to sync TSC|timeout attempting to get remote buffer space'
    if len(re.findall(bad,before))!=len(re.findall(bad,after)):raise RuntimeError('New RTIO fault during expired-start test')
    session.result.update(expired_result(log,raw[begin:].decode(errors='replace'),after))
