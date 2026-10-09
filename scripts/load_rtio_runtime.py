#!/usr/bin/env python3
"""Load matching local RTIO PL and both existing CPU images on an exact cable.

Volatile JTAG only; no card/flash changes. Captures FSBL and runtime UART.
"""
import argparse,subprocess,time,json,re
from pathlib import Path
import serial
REPO=Path(__file__).resolve().parent.parent
XSDB='/srv/codex-hil-data/toolchains/amd/Xilinx/2025.2/Vivado/bin/xsdb'
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for k in ('server','cable','port','ps-export','bitstream','worker','cpu0','output'):p.add_argument('--'+k,required=True)
 a=p.parse_args();out=Path(a.output);out.mkdir(parents=True,exist_ok=True)
 ps=Path(a.ps_export);w=Path(a.worker);raw=bytearray();logs={};result={'kind':'hardware-runtime-load','status':'FAIL'}
 def run(name,args):
  r=subprocess.run(args,capture_output=True,text=True,timeout=60);logs[name]=r.stdout+r.stderr;(out/(name+'.log')).write_text(logs[name])
  if r.returncode:raise RuntimeError(name+': '+logs[name])
  print(name+' PASS',flush=True)
 def xs(name,script,*args):run(name,['vivado-container','shell','-c','exec "$@"','bash',XSDB,str(REPO/script),*args])
 s=serial.Serial(a.port,115200,timeout=.2)
 try:
  s.reset_input_buffer()
  xs('reset','scripts/reset_genesys_ps.tcl',a.server,a.cable)
  xs('boot','scripts/run_boot_firmware.tcl',a.server,str(ps/'pmu-app/build/zynqmp_pmufw.elf'),str(ps/'app/build/zynqmp_fsbl.elf'),a.cable)
  deadline=time.monotonic()+30
  while time.monotonic()<deadline:
   raw.extend(s.read(s.in_waiting or 1))
   if b'Exit from FSBL' in raw:break
  else:raise RuntimeError('FSBL timeout')
  run('pl',['vivado','-mode','batch','-source',str(REPO/'scripts/program_genesys_pl.tcl'),'-tclargs',a.server.removeprefix('tcp:'),a.cable,a.bitstream])
  xs('prepare','scripts/prepare_local_rtio.tcl',a.server,str(ps/'sdt/psu_init.tcl'),a.cable)
  xs('cpu1','scripts/run_kernel_worker.tcl',a.server,str(w/'worker32.elf'),str(w/'start64.elf'),a.cable)
  xs('cpu0','scripts/run_a53_runtime.tcl',a.server,a.cpu0,a.cable)
  deadline=time.monotonic()+20
  while time.monotonic()<deadline:
   raw.extend(s.read(s.in_waiting or 1))
   if b'GENESYS kernel transport @ port 1381' in raw:break
  if b'GENESYS kernel transport @ port 1381' not in raw:raise RuntimeError('Kernel transport startup not confirmed: '+raw.decode(errors='replace')[-2500:])
  text=raw.decode(errors='replace');ips=re.findall(r'Board IP:\s*(\d+\.\d+\.\d+\.\d+)',text)
  if not ips:ips=re.findall(r'IP address\s*:\s*(\d+\.\d+\.\d+\.\d+)',text)
  if not ips:raise RuntimeError('No DHCP address in UART: '+text[-2500:])
  result.update(status='PASS',ip=ips[-1]);print('Runtime DHCP '+ips[-1],flush=True)
 except Exception as e:result['error']=str(e);print('FAIL',e,flush=True)
 finally:
  s.close();(out/'uart.log').write_bytes(raw);(out/'results.json').write_text(json.dumps(result,indent=2)+'\n')
 return 0 if result['status']=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
