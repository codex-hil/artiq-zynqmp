#!/usr/bin/env python3
"""Exercise autonomous firmware acquisition/loss/recovery and volatile restore.

Requires clock-forward diagnostic PL and matching boot/PS setup. Loads CPU0,
so all A53 cores must be available to this diagnostic, not running ARTIQ.
"""
import argparse,json,subprocess,time,hashlib
from pathlib import Path
import serial
REPO=Path(__file__).resolve().parents[2]
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for k in ('server','cable','port','elf','output'):p.add_argument('--'+k,required=True)
 p.add_argument('--cycles',type=int,default=3)
 a=p.parse_args()
 if a.cycles<1:p.error('cycles must be positive')
 out=Path(a.output);out.mkdir(parents=True,exist_ok=True)
 raw=bytearray();phase={};result={'kind':'physical-hardware','scope':'autonomous laboratory Si5342 manager over AMD XIicPs, internal GTH RX clock only','status':'FAIL','restored':False,'cycles':a.cycles}
 s=serial.Serial(a.port,115200,timeout=.2)
 def wait(name,marker,start,seconds=90):
  deadline=time.monotonic()+seconds
  while time.monotonic()<deadline:
   raw.extend(s.read(s.in_waiting or 1))
   if b'CLOCK FAIL' in raw[start:] or b'CLOCK RESTORE_FAIL' in raw[start:]:raise RuntimeError(raw[start:].decode(errors='replace'))
   if marker in raw[start:]:
    phase[name]=raw[start:].decode(errors='replace');print(name+' PASS',flush=True);return
  raise RuntimeError(name+' timeout: '+raw[start:].decode(errors='replace'))
 try:
  s.reset_input_buffer()
  r=subprocess.run(['vivado-container','shell','-c','exec "$@"','bash','/srv/codex-hil-data/toolchains/amd/Xilinx/2025.2/Vivado/bin/xsdb',str(REPO/'scripts/run_ethernet.tcl'),a.server,a.elf,a.cable],capture_output=True,text=True,timeout=60)
  (out/'load.log').write_text(r.stdout+r.stderr)
  if r.returncode:raise RuntimeError(r.stdout+r.stderr)
  wait('startup',b'CLOCK LOCKED',0)
  for i in range(a.cycles):
   start=len(raw);s.write(b'L');s.flush()
   wait('recovery-'+str(i),b'CLOCK LOCKED',start)
   segment=raw[start:]
   for marker in (b'CLOCK LOSS',b'CLOCK BOOTSTRAP',b'CLOCK PS_LOCK PASS',b'CLOCK RX_LOCK PASS',b'CLOCK PHY_PASS'):
    if marker not in segment:raise RuntimeError('Missing firmware transition '+str(marker))
  start=len(raw);s.write(b'Q');s.flush();wait('restore',b'CLOCK RESTORED',start)
  result['status']='PASS';result['restored']=True
 except Exception as e:
  result['error']=str(e);print('FAIL',e,flush=True)
  # Ask firmware to restore if it is still in its command loop.
  try:s.write(b'Q');s.flush()
  except Exception:pass
 finally:
  s.close();(out/'uart.log').write_bytes(raw)
  result['phases']=phase;result['elf_sha256']=hashlib.sha256(Path(a.elf).read_bytes()).hexdigest();result['uart_sha256']=hashlib.sha256(raw).hexdigest()
  result['production_runtime_integration']='NOT_RUN';result['remote_master']='NOT_RUN';result['jitter']='NOT_RUN'
  (out/'results.json').write_text(json.dumps(result,indent=2)+'\n')
 return 0 if result['status']=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
