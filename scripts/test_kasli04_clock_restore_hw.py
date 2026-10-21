"""Bounded KASLI04 clock qualification; preserve mode10 SRAM. LGPL-3.0-or-later."""
import argparse,fcntl,hashlib,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SECURE=Path('/home/codex-hil/kasli-secure-link')
DIAG=Path('/home/codex-hil/rng-rpi/kasli/artifacts/kasli-full-checker')
MODE10=SECURE/'build/sfp-identity-trace-reviewed-public-lab/kasli-sfp-identity-trace.bit'
DIAG_SHA='3db1e9398338e5f91d02a06a5b9f2a8923eb12d6f10c694708c0ce2c93894a15'
MODE10_SHA='66a52c71b4dfe6f987f219f85951a2b9abf931fb19ada3b4ce90da5b80d1e1ac'

def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--run',action='store_true');a=p.parse_args()
 sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'diagnostics/kasli-master'),str(SECURE/'scripts/hil')]
 from kasli_clock_binding import validate
 from run_paired_control_restore import Hardware
 from run_sfp_identity_trace import snapshot
 sys.path.insert(0,'/home/codex-hil/rng-rpi/kasli')
 from settled_i2c import SettledI2C
 from clock_restore import exercise
 from litex.tools.remote.comm_uart import CommUART
 baseline_file=ROOT/'evidence/kasli04-clock-cpu-2026-10-21/results.json'
 plan=json.loads((ROOT/'evidence/kasli04-clock-plan-2026-10-21/plan.json').read_text())
 source=Path('/srv/codex-hil-data/artiq-zynqmp/reference/artiq/artiq/firmware/libboard_artiq/si5324.rs').read_text()
 baseline=validate('KASLI04',plan,baseline_file,source)
 if plan['mux_addresses']!=[0x71]:raise ValueError('Absent mux70 must not be accessed')
 for path,sha in ((MODE10,MODE10_SHA),(DIAG/'gateware/kasli_diag.bit',DIAG_SHA)):
  if hashlib.sha256(path.read_bytes()).hexdigest()!=sha:raise ValueError('Restoration/diagnostic image changed')
 if not a.run:print('PREFLIGHT_PASS_NO_HARDWARE_ACCESS');return 0
 a.output.mkdir(parents=True,exist_ok=False)
 result=dict(status='FAIL',board='KASLI04',dna='0x006c440674704854',restoration='NOT_RUN',flash_written=False)
 b=dict(name='KASLI04',dna=result['dna'],usb='1-11.1');changed=False;comm=None;bus=None;saved_mux=None;saved_csr=None
 started=time.monotonic()
 class BoundedUART(CommUART):
  def _read(self,length):
   data=self.port.read(length)
   if len(data)!=length:raise TimeoutError('UARTBone short read')
   return data
  def write(self,*args,**kwargs):
   super().write(*args,**kwargs);self.port.flush()
 with open('/home/codex-hil/.cache/kasli-KASLI04.lock','a') as lock:
  try:
   fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
   hw=Hardware(a.output);hw.identify(b);result['before']=snapshot(hw,b)
   if result['before']['mode']!=10 or result['before']['version']!=0x1000c or result['before']['i2c_busy']:raise ValueError('Expected retained idle mode10')
   changed=True;hw.load(b,str(DIAG/'gateware/kasli_diag.bit'))
   comm=BoundedUART('/dev/serial/by-path/pci-0000:00:14.0-usb-0:11.1:1.2-port0',csr_csv=str(DIAG/'csr.csv'));comm.port.timeout=2;comm.open()
   if comm.regs.diag_identity.read()!=0x4b110001:raise ValueError('Wrong diagnostic identity')
   saved_csr=comm.regs.i2c_w.read();bus=SettledI2C(comm)
   bus.start()
   try:
    if not bus.put(0xe3):raise RuntimeError('Clock mux71 read NACK')
    saved_mux=bus.get(last=True)
   finally:bus.stop()
   bus.select_mux(0x71,8)
   fresh={}
   for reg in baseline['registers']:
    if time.monotonic()-started>110:raise TimeoutError('Fresh snapshot deadline')
    fresh[reg]=[bus.read(0x68,int(reg),1)[0] for _ in range(2)]
   result['fresh_registers']=fresh
   if fresh!=baseline['registers']:raise ValueError('Clock baseline changed; reset refused')
   result['clock_restore']={};exercise(comm,bus,fresh,plan,result['clock_restore']);result['status']='PASS'
  except BlockingIOError:result.update(status='BUSY',error='KASLI04 lease held; no hardware access')
  except Exception as error:result.update(status='FAIL',error=str(error))
  finally:
   if comm:
    try:
     if saved_mux is not None:
      bus.select_mux(0x71,saved_mux)
      bus.start()
      try:
       if not bus.put(0xe3) or bus.get(last=True)!=saved_mux:raise RuntimeError('Mux71 restore mismatch')
      finally:bus.stop()
     if saved_csr is not None:comm.regs.i2c_w.write(saved_csr)
     result['routing_restoration']='PASS'
    except Exception as error:result.update(status='FAIL',routing_restoration='FAIL',routing_error=str(error))
    finally:comm.close()
   if changed:
    try:
     if hashlib.sha256(MODE10.read_bytes()).hexdigest()!=MODE10_SHA:raise RuntimeError('Restore image changed')
     hw.load(b,str(MODE10));result['after']=snapshot(hw,b)
     if result['after']['version']!=0x1000c or result['after']['mode']!=10 or result['after']['i2c_busy']:raise RuntimeError('Mode10 restore mismatch')
     result['restoration']='PASS'
    except Exception as error:result.update(status='FAIL',restoration='FAIL',restore_error=str(error))
   result['session_seconds']=round(time.monotonic()-started,3)
   (a.output/'results.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(result,indent=2));return 0 if result['status']=='PASS' else 2

if __name__=='__main__':raise SystemExit(main())
