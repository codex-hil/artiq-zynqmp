"""Guarded native AUX DDMA playback (no DAP upload); LGPL-3.0-or-later."""
import json,re,time,runpy
from pathlib import Path


def validate(session,fw):
    c=session.config;mode=c.get('native_ddma_mode')
    if mode not in ('idle','playback') or session.host_dma_test or not session.dio_test or not session.snapshot_test:
        raise ValueError('Native DDMA requires explicit idle/playback mode, DIO/snapshot; no host DMA')
    if c.get('native_ddma_rejection') and (mode!='playback' or any(c.get(n) for n in
            ('native_ddma_lifecycle','native_ddma_fragmentation','native_ddma_long_lifecycle'))):
        raise ValueError('Rejection requires standalone native playback/recovery mode')
    if c.get('native_ddma_rejected_cleanup') and not c.get('native_ddma_rejection'):
        raise ValueError('Cleanup qualification requires native rejection/recovery mode')
    if c.get('native_ddma_structured_error') and not c.get('native_ddma_rejected_cleanup'):
        raise ValueError('Structured error qualification requires rejected cleanup/recovery mode')
    if c.get('native_ddma_catch') and (mode!='playback' or any(c.get(n) for n in
            ('native_ddma_rejection','native_ddma_rejected_cleanup','native_ddma_structured_error',
             'native_ddma_lifecycle','native_ddma_fragmentation','native_ddma_long_lifecycle'))):
        raise ValueError('Same-kernel catch requires standalone native playback mode')
    if c.get('native_ddma_cursor'):
        if not c.get('native_ddma_catch'):raise ValueError('Cursor test requires same-kernel catch')
        from prepare_dma_cursor_overlay import validate as validate_cursor
        validate_cursor(c['dma_cursor_overlay'])
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



def lifecycle_result(log,text):
    rows=re.findall(r'NATIVE_DDMA_LIFECYCLE_PASS phase=(\d+) replay=(\d+) edges=8 width_mu=(\d+) period_mu=(\d+) first_delta_mu=(\d+)',log)
    expected=[(p,r,8000*(p+1),80000+40000*p) for p in range(3) for r in range(3)]
    if len(rows)!=9 or [tuple(map(int,row[:4])) for row in rows]!=expected or not all(1000000<=int(row[4])<1100000 for row in rows):
        raise RuntimeError('Incomplete native lifecycle physical timestamps')
    events=[]
    for line in text.splitlines():
        m=re.fullmatch(r'AUX_DDMA REPLY kind=(177|181|179) id=(\d+) succeeded=1',line)
        if m:events.append((int(m[1]),int(m[2])))
        m=re.fullmatch(r'AUX_DDMA STATUS id=(\d+) error=0',line)
        if m:events.append((182,int(m[1])))
    pattern=[177,181,182,181,182,181,182,179]
    if (len(events)!=24 or text.count('AUX_DDMA REPLY')!=15 or text.count('AUX_DDMA STATUS')!=9 or
        [kind for kind,_ in events]!=pattern*3 or
        any(len({id for _,id in events[i:i+8]})!=1 for i in (0,8,16))):
        raise RuntimeError('Native lifecycle upload/playback/status/erase order mismatch')
    return dict(native_ddma_lifecycle='PASS',native_ddma_plays=9,native_ddma_edges=72,
        native_ddma_trace_ids=[events[i][1] for i in (0,8,16)],
        native_ddma_scope='three uploads, nine plays (six via handle), replacement plus erase/reupload; physical72 edges; no fragmentation/abort/phase proof')



def fragment_result(log,text):
    m=re.search(r'NATIVE_DDMA_FRAGMENT_PASS edges=58 width_mu=8000 period_mu=16000 first_delta_mu=(\d+)',log)
    if not m or not 1000000<=int(m[1])<1100000:raise RuntimeError('Fragmented physical capture absent')
    rows=re.findall(r'AUX_DDMA UPLOAD id=(\d+) status=(\d+) bytes=(\d+)',text)
    if len(rows)!=2 or [tuple(map(int,row[1:])) for row in rows]!=[(1,1010),(2,10)] or rows[0][0]!=rows[1][0]:
        raise RuntimeError('Expected two native upload fragments1010/10')
    id=rows[0][0]
    expected=[('177',id),('177',id),('181',id),('182',id),('179',id)]
    events=[]
    for line in text.splitlines():
        r=re.fullmatch(r'AUX_DDMA REPLY kind=(177|181|179) id=(\d+) succeeded=1',line)
        if r:events.append((r[1],r[2]))
        r=re.fullmatch(r'AUX_DDMA STATUS id=(\d+) error=0',line)
        if r:events.append(('182',r[1]))
    if events!=expected or text.count('AUX_DDMA REPLY')!=4 or text.count('AUX_DDMA STATUS')!=1:
        raise RuntimeError('Fragmented native operation sequence mismatch')
    return dict(native_ddma_fragmentation='PASS',native_ddma_edges=58,native_ddma_payload_bytes=1020,
        native_ddma_fragment_lengths=[1010,10],native_ddma_first_delta_mu=int(m[1]),
        native_ddma_scope='29 physical pulses after native two-packet upload across record boundary; no abort/phase/jitter qualification')



def long_lifecycle_result(log,text):
    rows=re.findall(r'NATIVE_DDMA_LONG_LIFECYCLE_PASS phase=(\d+) replay=(\d+) edges=58 width_mu=(\d+) period_mu=(\d+) first_delta_mu=(\d+)',log)
    expected=[(p,r,4000+p*2000,16000+p*4000) for p in range(3) for r in range(3)]
    if len(rows)!=9 or [tuple(map(int,row[:4])) for row in rows]!=expected or not all(1000000<=int(row[4])<1100000 for row in rows):
        raise RuntimeError('Incomplete long lifecycle physical timestamps')
    uploads=re.findall(r'AUX_DDMA UPLOAD id=(\d+) status=(\d+) bytes=(\d+)',text)
    if len(uploads)!=6 or [tuple(map(int,row[1:])) for row in uploads]!=[(1,1010),(2,10)]*3:
        raise RuntimeError('Long lifecycle requires three two-packet uploads')
    events=[]
    for line in text.splitlines():
        m=re.fullmatch(r'AUX_DDMA REPLY kind=(177|181|179) id=(\d+) succeeded=1',line)
        if m:events.append((int(m[1]),m[2]))
        m=re.fullmatch(r'AUX_DDMA STATUS id=(\d+) error=0',line)
        if m:events.append((182,m[1]))
    pattern=[177,177,181,182,181,182,181,182,179]
    if len(events)!=27 or text.count('AUX_DDMA REPLY')!=18 or text.count('AUX_DDMA STATUS')!=9 or [k for k,_ in events]!=pattern*3:
        raise RuntimeError('Long lifecycle operation order mismatch')
    for p in range(3):
        ids={id for _,id in events[9*p:9*p+9]}|{row[0] for row in uploads[2*p:2*p+2]}
        if len(ids)!=1:raise RuntimeError('Long lifecycle mixed trace IDs')
    return dict(native_ddma_long_lifecycle='PASS',native_ddma_plays=9,native_ddma_edges=522,
        native_ddma_fragment_lengths=[1010,10]*3,
        native_ddma_scope='three fragmented uploads, nine plays (six via handle), replacement/erase/reupload,522 physical edges; no abort/phase proof')


def probe(session,master_host,uart,raw):
    if session.config.get('native_ddma_catch'):
        from native_dma_catch_session import probe as catch_probe
        return catch_probe(session,master_host,uart,raw)
    c=session.config;out=session.output
    before=session.run('master-before-native-ddma-log',[c['artiq_python'],'-m','artiq.frontend.artiq_coremgmt','-D',master_host,'log'],timeout=15,host=True)
    db=runpy.run_path(str(out/'dio-device-db.py'))['device_db']
    db['core_dma']={'type':'local','module':'artiq.coredevice.dma','class':'CoreDMA'}
    path=out/'native-ddma-device-db.py';path.write_text('device_db = '+repr(db)+'\n')
    rejected=None;recovery_begin=0
    if c.get('native_ddma_rejection'):
        from native_dma_reject_session import attempt
        rejected=attempt(session,master_host,uart,raw,path)
        recovery_begin=len(raw)
    lifecycle=bool(c.get('native_ddma_lifecycle',False))
    fragment=bool(c.get('native_ddma_fragmentation',False))
    long_lifecycle=bool(c.get('native_ddma_long_lifecycle',False))
    if sum((fragment,lifecycle,long_lifecycle))>1:raise ValueError('Select one native DDMA experiment')
    example='kasli_drtio_native_dma_fragmented.py' if fragment else 'kasli_drtio_native_dma_lifecycle.py' if lifecycle else 'kasli_drtio_native_dma.py'
    if long_lifecycle:example='kasli_drtio_native_dma_long_lifecycle.py'
    log=session.run('master-native-ddma-probe',[c['artiq_python'],'-m','artiq.frontend.artiq_run',
        '--device-db='+str(path),'--dataset-db='+str(out/'native-ddma-datasets.mdb'),
        str(Path(__file__).resolve().parents[2]/'examples'/example)],timeout=60,host=True)
    match=re.search(r'NATIVE_DDMA_PHYSICAL_PASS edges=8 width_mu=8000 period_mu=80000 first_delta_mu=(\d+)',log)
    if not match and not lifecycle and not fragment and not long_lifecycle:raise RuntimeError('Native DDMA physical timestamps absent')
    end=time.monotonic()+1
    while time.monotonic()<end:raw.extend(uart.read(uart.in_waiting or 1))
    text=raw[recovery_begin:].decode(errors='replace')
    if rejected:session.result.update(rejected)
    adds=re.findall(r'AUX_DDMA REPLY kind=177 id=(\d+) succeeded=1',text)
    plays=re.findall(r'AUX_DDMA REPLY kind=181 id=(\d+) succeeded=1',text)
    status=re.findall(r'AUX_DDMA STATUS id=(\d+) error=0',text)
    removes=re.findall(r'AUX_DDMA REPLY kind=179 id=(\d+) succeeded=1',text)
    if c.get('native_ddma_rejected_cleanup'):
        from rejected_cleanup_evidence import cleanup_recovery_result
        cleanup_recovery_result(text,'',rejected['native_ddma_rejected_trace_id'])
        removes=removes[1:]  # identity-checked rejected cleanup, not final erase
    if not lifecycle and not fragment and not long_lifecycle and not (adds and len(plays)==len(status)==len(removes)==1 and plays==status==removes and set(adds)==set(plays)):
        raise RuntimeError('Missing native upload/playback/status/remove evidence')
    if any(t in text for t in ('AUX_DDMA FAIL_CLOSED','AUX_FW PANIC','AUX_SERVICE SEND_FAIL','AUX_SERVICE RX_ERROR')):
        raise RuntimeError('Native service fault')
    after=session.run('master-after-native-ddma-log',[c['artiq_python'],'-m','artiq.frontend.artiq_coremgmt','-D',master_host,'log'],timeout=15,host=True)
    if c.get('native_ddma_rejected_cleanup'):
        session.result.update(cleanup_recovery_result(text,after,rejected['native_ddma_rejected_trace_id']))
    if c.get('native_ddma_structured_error'):
        from structured_dma_evidence import structured_rejection_result
        session.result.update(structured_rejection_result((out/'master-native-ddma-rejection.log').read_text(),after,log))
    bad=r'reset failed|RTIO (?:sequence|collision|busy) error|failed to sync TSC|timeout attempting to get remote buffer space'
    if len(re.findall(bad,before))!=len(re.findall(bad,after)):raise RuntimeError('New master fault during DDMA')
    if long_lifecycle:
        session.result.update(long_lifecycle_result(log,text))
        session.result['native_ddma']='PASS'
        return
    if fragment:
        session.result.update(fragment_result(log,text))
        session.result['native_ddma']='PASS'
        return
    if lifecycle:
        session.result.update(lifecycle_result(log,text))
        session.result['native_ddma']='PASS'
        return
    session.result.update(native_ddma='PASS',native_ddma_edges=8,native_ddma_width_mu=8000,
        native_ddma_period_mu=80000,native_ddma_first_delta_mu=int(match[1]),native_ddma_id=int(plays[0]),
        native_ddma_scope='standard distributed CoreDMA -> native AUX upload/playback/status -> physical TTL; single trace; no abort/phase/jitter qualification')
