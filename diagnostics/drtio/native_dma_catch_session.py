"""Same-kernel upload exception/recovery proof; LGPL-3.0-or-later."""
import re,runpy,time
from pathlib import Path
from rejected_cleanup_evidence import cleanup_recovery_result


def catch_result(log,aux,master):
    physical=re.search(r'NATIVE_DDMA_PHYSICAL_PASS edges=8 width_mu=8000 period_mu=80000 first_delta_mu=(\d+)',log)
    if (log.count('NATIVE_DDMA_CAUGHT_PASS')!=1 or not physical or
            log.index('NATIVE_DDMA_CAUGHT_PASS')>physical.start() or
            not 1000000<=int(physical[1])<1100000):
        raise RuntimeError('Missing same-kernel catch followed by physical recovery')
    if ('ConnectionResetError' in log or 'Previous kernel did not cleanly finish' in log or
            'session aborted:' in master or 'DDMA upload rejected:' not in master):
        raise RuntimeError('Catch must not abort the kernel/session')
    uploads=re.findall(r'AUX_DDMA UPLOAD id=(\d+) status=(\d+) bytes=(\d+)',aux)
    if (len(uploads)!=3 or [tuple(map(int,r[1:])) for r in uploads]!=[(1,1010),(2,44),(3,170)] or
            uploads[0][0]!=uploads[1][0]):
        raise RuntimeError('Wrong negative/positive uploads')
    ident=uploads[0][0]
    nack=f'AUX_DDMA REPLY kind=177 id={ident} succeeded=0'
    if aux.count(nack)!=1:raise RuntimeError('Missing exact negative upload NACK')
    before,after=aux.split(nack,1)
    replies=re.findall(r'AUX_DDMA REPLY kind=(\d+) id=(\d+) succeeded=(\d+)',before)
    if replies!=[('177',ident,'1')] or 'AUX_DDMA STATUS' in before:
        raise RuntimeError('Rejected trace must not play')
    result=cleanup_recovery_result(after,master,int(ident))
    if result['native_ddma_recovery_id']!=int(uploads[2][0]):raise RuntimeError('Recovery ID mismatch')
    if any(t in aux for t in ('AUX_DDMA FAIL_CLOSED','AUX_FW PANIC','AUX_SERVICE SEND_FAIL','AUX_SERVICE RX_ERROR')):
        raise RuntimeError('Firmware fault during same-kernel recovery')
    result.update(native_ddma_same_kernel_catch='PASS',native_ddma='PASS',native_ddma_edges=8,
        native_ddma_first_delta_mu=int(physical[1]),native_ddma_catch_scope='one kernel and one initial core.reset; DMAError caught, break_realtime, same-name valid record/playback; no intervening reset/restart')
    return result


def probe(session,master_host,uart,raw):
    c=session.config;out=session.output;begin=len(raw)
    db=runpy.run_path(str(out/'dio-device-db.py'))['device_db']
    db['core_dma']={'type':'local','module':'artiq.coredevice.dma','class':'CoreDMA'}
    path=out/'catch-device-db.py';path.write_text('device_db = '+repr(db)+'\n')
    before=session.run('master-before-catch-log',[c['artiq_python'],'-m','artiq.frontend.artiq_coremgmt','-D',master_host,'log'],timeout=15,host=True)
    example='kasli_drtio_native_dma_cursor.py' if c.get('native_ddma_cursor') else 'kasli_drtio_native_dma_catch.py'
    command=[c['artiq_python'],'-m','artiq.frontend.artiq_run',
        '--device-db='+str(path),'--dataset-db='+str(out/'catch-datasets.mdb'),
        str(Path(__file__).resolve().parents[2]/'examples'/example)]
    if c.get('native_ddma_cursor'):
        from prepare_dma_cursor_overlay import validate
        validate(c['dma_cursor_overlay'])
        command=['env','PYTHONPATH='+str(Path(c['dma_cursor_overlay']).resolve()),*command]
    log=session.run('master-native-catch-probe',command,timeout=60,host=True)
    end=time.monotonic()+1
    while time.monotonic()<end:raw.extend(uart.read(uart.in_waiting or 1))
    after=session.run('master-after-catch-log',[c['artiq_python'],'-m','artiq.frontend.artiq_coremgmt','-D',master_host,'log'],timeout=15,host=True)
    bad=r'reset failed|RTIO (?:sequence|collision|busy) error|failed to sync TSC|timeout attempting to get remote buffer space'
    if len(re.findall(bad,before))!=len(re.findall(bad,after)):raise RuntimeError('New RTIO fault during catch')
    session.result.update(catch_result(log,raw[begin:].decode(errors='replace'),after))
    if c.get('native_ddma_cursor'):
        marker='NATIVE_DDMA_CURSOR_PASS success=1 failure=1'
        if log.count(marker)!=1 or log.index(marker)>log.index('NATIVE_DDMA_PHYSICAL_PASS'):
            raise RuntimeError('Missing exception/success cursor checks before playback')
        session.result['native_ddma_cursor_restoration']='PASS'
        session.result['native_ddma_cursor_scope']='exact saved now before resynchronization on both exits; isolated host finally overlay'
