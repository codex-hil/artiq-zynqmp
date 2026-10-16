"""Guarded host-armed DDR DMA stage, not native AUX DDMA; LGPL-3.0-or-later."""
import json,re,time
from pathlib import Path


def validate(session):
    if not session.dio_test or not session.mapping.get('dma'):
        raise ValueError('Host DMA requires actual satellite DMA target and DIO stage')
    proof=json.loads(Path(session.config['dma_idle_qualification']).read_text())
    external=proof.get('external_rx',{})
    if (proof.get('status')!='PASS' or proof.get('restoration')!='PASS' or
        external.get('dio_loopback')!='PASS' or external.get('restoration')!='PASS' or
        external.get('bit_sha256')!=session.result['bit_sha256'] or
        external.get('firmware_sha256')!=session.result['firmware_sha256']):
        raise ValueError('Exact bit/firmware must first pass guarded physical cold release/DIO')


def probe(session,master_host,uart,raw):
    c=session.config;out=session.output
    # run() keeps inherited parent lease FD for the host RPC process. The parent
    # additionally holds all Kasli leases through validation and restoration.
    before=session.run('master-before-ddr-dma-log',[c['artiq_python'],'-m',
        'artiq.frontend.artiq_coremgmt','-D',master_host,'log'],timeout=15,host=True)
    config=out/'dma-config.json';config.write_text(json.dumps(c,indent=2)+'\n')
    log=session.run('master-ddr-dma-probe',['env',
        'SATELLITE_DMA_CONFIG='+str(config.resolve()),
        'SATELLITE_DMA_OUTPUT='+str((out/'dma-playback').resolve()),
        c['artiq_python'],'-m','artiq.frontend.artiq_run',
        '--device-db='+str(out/'dio-device-db.py'),
        '--dataset-db='+str(out/'dma-datasets.mdb'),
        str(Path(__file__).resolve().parents[2]/'examples/kasli_drtio_dma_diagnostic.py')],
        timeout=75,host=True)
    match=re.search(r'SATELLITE_DDR_DMA_PHYSICAL_PASS edges=8 width_mu=8000 period_mu=80000 first_delta_mu=(\d+)',log)
    if not match:raise RuntimeError('Missing physical DDR DMA timestamps')
    admitted=(out/'dma-playback/probe.log').read_text()
    if 'SATELLITE_DDR_DMA_ADMITTED_PASS bursts_limit=16 readback_bytes=2048' not in admitted:
        raise RuntimeError('Missing actual DMA admission/readback evidence')
    end=time.monotonic()+1
    while time.monotonic()<end:raw.extend(uart.read(uart.in_waiting or 1))
    after=session.run('master-after-ddr-dma-log',[c['artiq_python'],'-m',
        'artiq.frontend.artiq_coremgmt','-D',master_host,'log'],timeout=15,host=True)
    bad=r'reset failed|RTIO (?:sequence|collision|busy) error|failed to sync TSC|timeout attempting to get remote buffer space'
    if len(re.findall(bad,after))!=len(re.findall(bad,before)):
        raise RuntimeError('New master error during host DDR DMA')
    if any(token in raw for token in (b'AUX_FW PANIC',b'AUX_RESET REJECT',b'AUX_SERVICE SEND_FAIL',b'AUX_SERVICE RX_ERROR')):
        raise RuntimeError('Satellite firmware fault during DDR DMA')
    session.result.update(ddr_dma_loopback='PASS',ddr_dma_pulses=4,ddr_dma_edges=8,
        ddr_dma_width_mu=8000,ddr_dma_period_mu=80000,ddr_dma_first_delta_mu=int(match[1]),
        ddr_dma_scope='host DAP writes/reads back DDR and arms native PL DMA; physical loopback read via standard Kasli kernel; NOT native AUX DDMA; no abort/absolute phase proof')
