#!/usr/bin/env python3
"""Load separate DRTIO diagnostic PL on the verified Genesys cable.

Volatile JTAG only; no card/flash changes. Captures FSBL and runtime UART.
"""
import argparse,subprocess,time,json,re
from pathlib import Path
import serial
REPO=Path(__file__).resolve().parent.parent
XSDB='/srv/codex-hil-data/toolchains/amd/Xilinx/2025.2/Vivado/bin/xsdb'
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for k in ('server','cable','port','ps-export','bitstream','output'):p.add_argument('--'+k,required=True)
 a=p.parse_args()
 if a.cable != '210383B7F02DA':p.error('Only verified Genesys cable is supported')
 out=Path(a.output);out.mkdir(parents=True,exist_ok=True)
 ps=Path(a.ps_export);raw=bytearray();logs={};result={'kind':'hardware-diagnostic-load','status':'FAIL'}
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
  xs('prepare','diagnostics/drtio/prepare_ps.tcl',a.server,str(ps/'sdt/psu_init.tcl'),a.cable)
  result.update(status='PASS',a53s='halted');print('DRTIO diagnostic loaded; A53s halted',flush=True)
 except Exception as e:result['error']=str(e);print('FAIL',e,flush=True)
 finally:
  s.close();(out/'uart.log').write_bytes(raw);(out/'results.json').write_text(json.dumps(result,indent=2)+'\n')
 return 0 if result['status']=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
