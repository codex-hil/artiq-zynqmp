"""Guarded host-only DMA abort observation; LGPL-3.0-or-later."""
import json,re,time
from pathlib import Path


def probe(session,master_host,uart,raw):
    c=session.config;out=session.output
    before=session.run('master-before-abort-log',[c['artiq_python'],'-m',
        'artiq.frontend.artiq_coremgmt','-D',master_host,'log'],timeout=15,host=True)
    config=out/'abort-config.json';config.write_text(json.dumps(c,indent=2)+'\n')
    text=session.run('master-abort-probe',['env',
        'SATELLITE_DMA_CONFIG='+str(config.resolve()),
        'SATELLITE_DMA_OUTPUT='+str((out/'abort-playback').resolve()),
        c['artiq_python'],'-m','artiq.frontend.artiq_run',
        '--device-db='+str(out/'dio-device-db.py'),
        '--dataset-db='+str(out/'abort-datasets.mdb'),
        str(Path(__file__).resolve().parents[2]/'examples/kasli_drtio_dma_abort.py')],
        timeout=75,host=True)
    if 'SATELLITE_DMA_ABORT_PHYSICAL_PASS canceled_edges=0 packet_edges=2 width_mu=8000' not in text:
        raise RuntimeError('Missing physical abort observation')
    admitted=(out/'abort-playback/probe.log').read_text()
    if 'SATELLITE_DMA_ABORT_DRAIN_PASS bytes=32768 bursts_limit=256 error=1' not in admitted:
        raise RuntimeError('Missing actual DMA abort/drain proof')
    if (out/'abort-playback/trace.bin').read_bytes()!=(out/'abort-playback/readback.bin').read_bytes():
        raise RuntimeError('Abort DDR readback changed')
    end=time.monotonic()+1
    while time.monotonic()<end:raw.extend(uart.read(uart.in_waiting or 1))
    after=session.run('master-after-abort-log',[c['artiq_python'],'-m',
        'artiq.frontend.artiq_coremgmt','-D',master_host,'log'],timeout=15,host=True)
    bad=r'reset failed|RTIO (?:sequence|collision|busy) error|failed to sync TSC|timeout attempting to get remote buffer space'
    if len(re.findall(bad,after))!=len(re.findall(bad,before)):
        raise RuntimeError('New master error during abort diagnostic')
    if any(token in raw for token in (b'AUX_FW PANIC',b'AUX_RESET REJECT',b'AUX_SERVICE SEND_FAIL',b'AUX_SERVICE RX_ERROR')):
        raise RuntimeError('Satellite firmware fault during abort diagnostic')
    session.result.update(dma_abort='PASS',dma_abort_canceled_edges=0,dma_abort_packet_edges=2,
        dma_abort_scope='host-only DAP start/abort; post-recovery input rearm, all future trace timestamps observed, native packet pulse without DMA restart/core reset; no paused-clock fault injection')
