"""Guarded native AUX DDMA playback (no DAP upload); LGPL-3.0-or-later."""
import json,re,time,runpy
from pathlib import Path


def validate(session,fw):
    c=session.config;mode=c.get('native_ddma_mode')
    if mode not in ('idle','playback') or session.host_dma_test or not session.dio_test or not session.snapshot_test:
        raise ValueError('Native DDMA requires explicit idle/playback mode, DIO/snapshot; no host DMA')
    for name in ('ddma_runtime.h','ddma_service.h','ddma_store.h','ddma_backend.h','ddma_a53.h','ddma_codec.h'):
        import hashlib
        if fw.get('ddma_sources',{}).get(name)!=hashlib.sha256((Path(__file__).parent/'aux_protocol'/name).read_bytes()).hexdigest():
            raise ValueError('Stale native DDMA helper: '+name)
    if mode=='playback':
        proof=json.loads(Path(c['ddma_idle_qualification']).read_text());ext=proof.get('external_rx',{})
        if (proof.get('status')!='PASS' or proof.get('restoration')!='PASS' or
            any(ext.get(k)!='PASS' for k in ('restoration','dio_loopback','tsc_snapshot')) or
            ext.get('bit_sha256')!=session.result['bit_sha256'] or
            ext.get('firmware_sha256')!=session.result['firmware_sha256']):
            raise ValueError('Native DDMA requires exact prior idle/snapshot/DIO/restoration proof')


def probe(session,master_host,uart,raw):
    c=session.config;out=session.output
    before=session.run('master-before-native-ddma-log',[c['artiq_python'],'-m','artiq.frontend.artiq_coremgmt','-D',master_host,'log'],timeout=15,host=True)
    db=runpy.run_path(str(out/'dio-device-db.py'))['device_db']
    db['core_dma']={'type':'local','module':'artiq.coredevice.dma','class':'CoreDMA'}
    path=out/'native-ddma-device-db.py';path.write_text('device_db = '+repr(db)+'\n')
    log=session.run('master-native-ddma-probe',[c['artiq_python'],'-m','artiq.frontend.artiq_run',
        '--device-db='+str(path),'--dataset-db='+str(out/'native-ddma-datasets.mdb'),
        str(Path(__file__).resolve().parents[2]/'examples/kasli_drtio_native_dma.py')],timeout=60,host=True)
    match=re.search(r'NATIVE_DDMA_PHYSICAL_PASS edges=8 width_mu=8000 period_mu=80000 first_delta_mu=(\d+)',log)
    if not match:raise RuntimeError('Native DDMA physical timestamps absent')
    end=time.monotonic()+1
    while time.monotonic()<end:raw.extend(uart.read(uart.in_waiting or 1))
    text=raw.decode(errors='replace')
    adds=re.findall(r'AUX_DDMA REPLY kind=177 id=(\d+) succeeded=1',text)
    plays=re.findall(r'AUX_DDMA REPLY kind=181 id=(\d+) succeeded=1',text)
    status=re.findall(r'AUX_DDMA STATUS id=(\d+) error=0',text)
    removes=re.findall(r'AUX_DDMA REPLY kind=179 id=(\d+) succeeded=1',text)
    if not (adds and len(plays)==len(status)==len(removes)==1 and plays==status==removes and set(adds)==set(plays)):
        raise RuntimeError('Missing native upload/playback/status/remove evidence')
    if any(t in text for t in ('AUX_DDMA FAIL_CLOSED','AUX_FW PANIC','AUX_SERVICE SEND_FAIL','AUX_SERVICE RX_ERROR')):
        raise RuntimeError('Native service fault')
    after=session.run('master-after-native-ddma-log',[c['artiq_python'],'-m','artiq.frontend.artiq_coremgmt','-D',master_host,'log'],timeout=15,host=True)
    bad=r'reset failed|RTIO (?:sequence|collision|busy) error|failed to sync TSC|timeout attempting to get remote buffer space'
    if len(re.findall(bad,before))!=len(re.findall(bad,after)):raise RuntimeError('New master fault during DDMA')
    session.result.update(native_ddma='PASS',native_ddma_edges=8,native_ddma_width_mu=8000,
        native_ddma_period_mu=80000,native_ddma_first_delta_mu=int(match[1]),native_ddma_id=int(plays[0]),
        native_ddma_scope='standard distributed CoreDMA -> native AUX upload/playback/status -> physical TTL; single trace; no abort/phase/jitter qualification')
