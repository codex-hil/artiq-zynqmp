"""Fixed KASLI04 clock read, absent EEM mux omitted. LGPL-3.0-or-later."""
from pathlib import Path
import sys,json,fcntl,hashlib,re
sys.path.insert(0,'/home/codex-hil/kasli-secure-link/scripts/hil')
from read_sfp_ftdi import FixedBus
from run_paired_control_restore import Hardware
from run_sfp_identity_trace import snapshot
out=Path(__file__).resolve().parent
b=dict(name='KASLI04',dna='0x006c440674704854',usb='1-11.1')
r=dict(status='FAIL',board='KASLI04',clock_configuration_written=False,absent_eem_mux='0x70: physically removed; not accessed',registers={})
with open('/home/codex-hil/.cache/kasli-KASLI04.lock','a') as h:
 try:
  fcntl.flock(h,fcntl.LOCK_EX|fcntl.LOCK_NB)
  hw=Hardware(out);hw.identify(b);before=snapshot(hw,b);r['before']=before
  if before['mode']!=10 or before['i2c_busy']:raise RuntimeError('Expected idle retained mode10')
  source=Path('/srv/codex-hil-data/artiq-zynqmp/reference/artiq/artiq/firmware/libboard_artiq/si5324.rs').read_text()
  regs=sorted({int(x) for x in re.findall(r'\b(?:read|write|write_no_ack_value)\((\d+)',source)})
  bus=FixedBus();saved=None
  try:
   usb=Path('/sys/bus/usb/devices/1-11.1');url=f'ftdi://ftdi:4232h:{int((usb/"busnum").read_text()):x}:{int((usb/"devnum").read_text()):x}/2'
   bus.configure(url);bus.acquire();saved=bus.read_single(0x71);r['prior_mux71']=saved
   bus.write_single(0x71,8)
   for reg in regs:r['registers'][str(reg)]=[bus.read_many(0x68,reg,1)[0] for _ in range(2)]
   r['changed_registers']=[k for k,v in r['registers'].items() if v[0]!=v[1]]
   if (r['registers']['134'][0]<<8|r['registers']['135'][0])!=0x182:raise RuntimeError('Wrong Si5324 identity')
   if r['changed_registers']:raise RuntimeError('Unstable clock snapshot')
   if any(v&1 for v in r['registers']['130']):raise RuntimeError('Si5324 unlocked')
   r.update(status='PASS',dna=b['dna'],si_source_sha256=hashlib.sha256(source.encode()).hexdigest())
  finally:
   try:
    if saved is not None:
     bus.write_single(0x71,saved)
     if bus.read_single(0x71)!=saved:raise RuntimeError('Mux71 restoration mismatch')
     r['routing_restoration']='PASS'
   finally:
    bus.release_lines();bus.dev.close()
  r['after']=snapshot(hw,b)
 except BlockingIOError:r.update(status='BUSY',error='KASLI04 shared lease busy')
 except Exception as e:r.update(status='FAIL',error=str(e))
(out/'results.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
raise SystemExit(0 if r['status']=='PASS' else 2)
