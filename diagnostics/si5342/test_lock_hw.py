#!/usr/bin/env python3
"""Physical RX clock presence/lock/loss/reacquisition, restoring all touched settings.
Requires clock-forward diagnostic PL, acquired PMA loopback and UART service.
No OTP access. This is a self-referential laboratory clock test, not remote DRTIO.
"""
import argparse
import json
from pathlib import Path
import subprocess
import re
import time
from client import Client
from validate_profile import validate

HERE=Path(__file__).resolve().parent

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('port','server','cable','csr-map','output'):p.add_argument('--'+name,required=True)
 p.add_argument('--profile',default=str(HERE/'profile-rx125.json'))
 p.add_argument('--cycles',type=int,default=3)
 p.add_argument('--seed-bootstrap',action='store_true')
 p.add_argument('--reset-clock-chip',action='store_true')
 a=p.parse_args()
 if a.cycles<1:p.error('--cycles must be positive')
 out=Path(a.output);out.mkdir(parents=True,exist_ok=True)
 mapping=json.loads(Path(a.csr_map).read_text())
 assert mapping['magic']==0x44525430
 forward=mapping['registers']['monitor_forward_enable']['address']
 assert forward==0xa0000030
 profile=json.loads(Path(a.profile).read_text())
 writes={int(k,16):v for k,v in profile['writes'].items()}
 log=(out/'uart.log').open('a'); c=Client(a.port,log)
 evidence={'kind':'physical-hardware','scope':'internal GTH PMA RXCLK -> Si5342 IN0; no remote master or jitter/deterministic latency measurement','profile':profile,'cycles':[],'status':'FAIL','restored':False}
 saved={};started=False
 def csr(op,val=0):
  r=subprocess.run(['vivado-container','shell','-c','exec "$@"','bash','/srv/codex-hil-data/toolchains/amd/Xilinx/2025.2/Vivado/bin/xsdb',str(HERE/'clock_csr.tcl'),a.server,a.cable,op,str(val),hex(forward)],capture_output=True,text=True,timeout=30)
  with (out/'jtag.log').open('a') as f:f.write(r.stdout+r.stderr)
  if r.returncode:raise RuntimeError(r.stdout+r.stderr)
  return r.stdout
 def gth_snapshot():
  raw=csr('snapshot')
  rows=re.findall(r'^CLOCK_SNAPSHOT (\d+) (\d+) (\d+) (\d+) (\d+)$',raw,re.M)
  if len(rows)!=1:raise RuntimeError(raw)
  return tuple(map(int,rows[0]))
 def verify_gth():
  before=gth_snapshot();time.sleep(1);after=gth_snapshot()
  deltas=[(after[i]-before[i])&0xffffffff for i in range(1,5)]
  if after[0]&0x7f!=0x7f or before[0]&0x7f!=0x7f:raise RuntimeError('GTH not ready')
  if deltas[3]!=0:raise RuntimeError('Settled PRBS7 errors: '+str(deltas))
  if not 1000000<deltas[0]<2000000000 or any(abs(float(deltas[i])/deltas[0]-1)>0.001 for i in (1,2)):
   raise RuntimeError('RX/TX clock activity invalid: '+str(deltas))
  return {'before':before,'after':after,'deltas_boot_rx_tx_errors':deltas}
 def status():
  return {'time':time.time(),'internal':c.read(0xc),'inputs':c.read(0xd),'pll':c.read(0xe),'cal':c.read(0xf),'active':c.read(0x507)}
 def wait(label,predicate,seconds=20):
  samples=[];deadline=time.monotonic()+seconds;consecutive=0
  while time.monotonic()<deadline:
   sample=status();samples.append(sample)
   consecutive=consecutive+1 if predicate(sample) else 0
   if consecutive>=5:
    evidence.setdefault('phases',[]).append({'name':label,'samples':samples}); print(label,sample,flush=True);return sample
   time.sleep(.2)
  evidence.setdefault('phases',[]).append({'name':label,'samples':samples});raise RuntimeError(f'{label} timeout: {samples[-1]}')
 def preamble():
  c.checked_write(0xb24,0xc0);c.checked_write(0xb25,0);c.checked_write(0x540,1);time.sleep(.3)
 def finish():
  c.write(0x514,1);c.write(0x1c,1);time.sleep(.05)
  c.checked_write(0x540,0);c.checked_write(0xb24,0xc3);c.checked_write(0xb25,2)
 try:
  assert c.read(2)==0x42 and c.read(3)==0x53
  if a.reset_clock_chip:
   response=c.command('W001E02','WRITE ')
   if response[1:3]!=['001E','02'] or int(response[3]) not in (0,-1):raise RuntimeError(response)
   time.sleep(.5);c.write(0x1e,0);time.sleep(.3)
   evidence['clock_chip_hard_reset']=True
   assert c.read(0xfe)==0x0f
  # Preserve frequency plan; this profile is specific to factory156.25MHz.
  baseline=json.loads((HERE/'factory-plan.json').read_text())
  evidence['arithmetic']=validate(profile,baseline)
  for k,v in baseline.items():
   if c.read(int(k,16))!=v:raise RuntimeError('Unexpected factory output plan: '+k)
  for reg in sorted(set(writes)|{0xb24,0xb25,0x540}):saved[reg]=c.read(reg)
  (out/'before.json').write_text(json.dumps({f'{k:04x}':v for k,v in saved.items()},indent=2)+'\n')
  evidence['initial']=status();started=True
  csr('restart')
  evidence['baseline_gth']=verify_gth()
  if a.seed_bootstrap:
   assert mapping['registers']['monitor_forward_bootstrap']['address']==0xa0000034
   csr('source',1)
   evidence['seed_source']='independent-PS-125MHz'
  csr('gate',0)
  preamble()
  for reg,value in sorted(writes.items()):c.checked_write(reg,value)
  finish()
  wait('input0-clock-off',lambda s:bool(s['inputs']&1))
  csr('gate',1)
  wait('input0-clock-on',lambda s:not(s['inputs']&1))
  locked=lambda s: not(s['pll']&0x22) and not(s['inputs']&0x11) and not(s['internal']&0x0b) and not(s['cal']&0x20) and (s['active']>>6)==0
  wait('initial-lock',locked,60)
  csr('restart')
  if a.seed_bootstrap:
   csr('source',0)
   wait('switch-to-rx-lock',locked,60)
  evidence['initial_gth']=verify_gth()
  for i in range(a.cycles):
   csr('gate',0)
   loss=wait(f'loss-{i}',lambda s:bool(s['inputs']&1) and bool(s['pll']&0x22))
   csr('gate',1)
   relock=wait(f'relock-{i}',locked,60)
   evidence['cycles'].append({'loss':loss,'relock':relock,'gth':verify_gth()})
  evidence['status']='PASS'
 except Exception as exc:
  evidence['error']=str(exc);print('FAIL',exc,flush=True)
  if started:
   try:
    evidence['failure_readback']={f'{reg:04x}':c.read(reg) for reg in writes}
   except Exception as read_exc:evidence['failure_readback_error']=str(read_exc)
 finally:
  if started:
   try:
    csr('gate',0)
    if a.seed_bootstrap:csr('source',0)
    preamble()
    for reg,value in sorted(saved.items()):
     if reg not in (0xb24,0xb25,0x540):c.checked_write(reg,value)
    finish()
    for reg in (0x540,0xb24,0xb25):c.checked_write(reg,saved[reg])
    evidence['restore_status']=status();evidence['restored']=True
   except Exception as exc:evidence['restore_error']=str(exc);evidence['status']='FAIL'
  c.close();log.close();(out/'results.json').write_text(json.dumps(evidence,indent=2)+'\n')
 print(json.dumps({k:v for k,v in evidence.items() if k not in ('profile','phases')},indent=2))
 return 0 if evidence['status']=='PASS' and evidence['restored'] else 1

if __name__=='__main__':raise SystemExit(main())
