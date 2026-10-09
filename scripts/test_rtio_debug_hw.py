#!/usr/bin/env python3
"""Use standard ARTIQ clients to validate physical analyzer and MonInj.

Requires debug PL/runtime and fitted JB1->JB2 jumper. TTL transitions occur.
"""
import argparse,asyncio,json,subprocess,time,hashlib,socket
from pathlib import Path
from artiq.coredevice.comm_moninj import CommMonInj
from artiq.coredevice.comm_analyzer import get_analyzer_dump,decode_dump,OutputMessage,InputMessage,StoppedMessage

async def moninj(ip):
    probes={};injections={};events=[]
    def monitor(ch,p,v):probes[(ch,p)]=v;events.append(('probe',ch,p,v))
    def inject(ch,o,v):injections[(ch,o)]=v;events.append(('injection',ch,o,v))
    async def until(predicate,label):
        deadline=time.monotonic()+4
        while time.monotonic()<deadline:
            if predicate():return
            await asyncio.sleep(.05)
        raise RuntimeError(label+': '+repr(events[-12:]))
    c=CommMonInj(monitor,inject)
    await c.connect(ip)
    try:
        c.monitor_probe(True,0,0);c.monitor_probe(True,1,0)
        c.monitor_injection(True,0,0);c.monitor_injection(True,0,1)
        await until(lambda:len(probes)==2,'initial subscriptions')
        print('moninj subscriptions PASS',flush=True)
        for v in (1,0,1):
            c.inject(0,1,v);c.inject(0,0,1)
            await until(lambda:probes.get((0,0))==v and probes.get((1,0))==v,'physical output/input '+str(v))
            c.get_injection_status(0,0);c.get_injection_status(0,1)
            await until(lambda:injections.get((0,0))==1 and injections.get((0,1))==v,'override readback')
            print('moninj physical level '+str(v)+' PASS',flush=True)
    finally:await c.close()
    # Closing a client must release its override; physical pins return low.
    # The upstream client closes its writer without waiting for peer FIN.
    await asyncio.sleep(.3)
    probes.clear();c=CommMonInj(monitor,inject);await c.connect(ip)
    try:
        c.monitor_probe(True,0,0);c.monitor_probe(True,1,0)
        await until(lambda:probes.get((0,0))==0 and probes.get((1,0))==0,'disconnect override cleanup')
    finally:await c.close()
    return events

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--ip',required=True);p.add_argument('--device-db',type=Path,required=True)
    p.add_argument('--artiq-run',default='artiq_run');p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
    result={'kind':'physical-hardware','status':'FAIL','ip':a.ip,'scope':'finite BRAM analyzer and local TTL MonInj using standard ARTIQ clients'}
    try:
        # Bad magic must not consume the only moninj slot indefinitely.
        with socket.create_connection((a.ip,1383),timeout=3) as s:
            s.sendall(b'INVALID moninj\n')
            try:
                if s.recv(1):raise RuntimeError('invalid handshake returned data')
            except ConnectionResetError:pass
        time.sleep(.2)
        result['moninj_events']=asyncio.run(moninj(a.ip))
        # Clear prior capture, then execute normal CoreDMA experiment.
        decode_dump(get_analyzer_dump(a.ip))
        repo=Path(__file__).resolve().parent.parent
        r=subprocess.run([a.artiq_run,'--device-db',str(a.device_db.resolve()),str(repo/'examples/genesys_dma.py')],cwd=a.output,capture_output=True,text=True,timeout=60)
        (a.output/'dma.log').write_text(r.stdout+r.stderr)
        if r.returncode or r.stdout.count('COREDMA_LOOPBACK_PASS')!=2:raise RuntimeError(r.stdout+r.stderr)
        raw=get_analyzer_dump(a.ip);(a.output/'analyzer.bin').write_bytes(raw);d=decode_dump(raw)
        outputs=[m for m in d.messages if isinstance(m,OutputMessage) and m.channel==0]
        inputs=[m for m in d.messages if isinstance(m,InputMessage) and m.channel==1]
        if len(outputs)<16 or len(inputs)<16:raise RuntimeError('Expected physical DMA TTL output/input records: '+repr(d.messages))
        if not isinstance(d.messages[-1],StoppedMessage):raise RuntimeError('Missing analyzer stop marker')
        if {m.data for m in outputs}!={0,1}:raise RuntimeError('Missing TTL high/low output data')
        result['analyzer']={'bytes':len(raw),'messages':len(d.messages),'ttl_outputs':len(outputs),'ttl_inputs':len(inputs),'sha256':hashlib.sha256(raw).hexdigest()}
        # New connection must return a clean restarted capture, without old TTL.
        next_dump=decode_dump(get_analyzer_dump(a.ip))
        if any(isinstance(m,(OutputMessage,InputMessage)) for m in next_dump.messages):raise RuntimeError('Analyzer capture did not reset')
        # Fill beyond 256 records and exercise multi-segment TCP delivery.
        for i in range(8):
            r=subprocess.run([a.artiq_run,'--device-db',str(a.device_db.resolve()),str(repo/'examples/genesys_dma.py')],cwd=a.output,capture_output=True,text=True,timeout=60)
            (a.output/('wrap-dma-'+str(i)+'.log')).write_text(r.stdout+r.stderr)
            if r.returncode or r.stdout.count('COREDMA_LOOPBACK_PASS')!=2:raise RuntimeError('DMA ring-fill experiment failed: '+r.stdout+r.stderr)
        raw=get_analyzer_dump(a.ip);(a.output/'analyzer-wrapped.bin').write_bytes(raw);wrapped=decode_dump(raw)
        total=int.from_bytes(raw[5:13],'big')
        if len(wrapped.messages)!=256 or total<=8192:raise RuntimeError('Expected wrapped 256-record analyzer ring')
        if not isinstance(wrapped.messages[-1],StoppedMessage):raise RuntimeError('Wrapped capture lacks final stop')
        result['wrapped_analyzer']={'bytes':len(raw),'messages':len(wrapped.messages),'total_bytes':total,'sha256':hashlib.sha256(raw).hexdigest()}
        result['dma_experiments']=9
        result['status']='PASS' 
    except Exception as e:result['error']=str(e);print('FAIL',e)
    (a.output/'results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
    return 0 if result['status']=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
