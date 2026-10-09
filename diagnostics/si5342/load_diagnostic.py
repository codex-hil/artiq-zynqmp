#!/usr/bin/env python3
"""Reset the exact Genesys, boot existing PMU/FSBL, load clock diagnostic and service."""
import argparse
from pathlib import Path
import subprocess
import time
import serial

REPO=Path(__file__).resolve().parents[2]
XSDB='/srv/codex-hil-data/toolchains/amd/Xilinx/2025.2/Vivado/bin/xsdb'

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('server','cable','port','ps-export','bitstream','csr-map','output'):
  p.add_argument('--'+name,required=True)
 p.add_argument('--service-elf', help='Optional Si5342 UART service; omit for halted-CPU GTH protocol tests')
 a=p.parse_args();out=Path(a.output);out.mkdir(parents=True,exist_ok=True)
 ps=Path(a.ps_export)
 def run(name,args):
  r=subprocess.run(args,capture_output=True,text=True,timeout=60)
  (out/(name+'.log')).write_text(r.stdout+r.stderr)
  if r.returncode:raise RuntimeError(name+': '+r.stdout+r.stderr)
  print(name+' PASS',flush=True)
 def xs(name,script,*args):
  run(name,['vivado-container','shell','-c','exec "$@"','bash',XSDB,str(REPO/script),*args])
 uart=serial.Serial(a.port,115200,timeout=.2);raw=bytearray()
 try:
  xs('reset','scripts/reset_genesys_ps.tcl',a.server,a.cable)
  xs('boot','scripts/run_boot_firmware.tcl',a.server,
     str(ps/'pmu-app/build/zynqmp_pmufw.elf'),str(ps/'app/build/zynqmp_fsbl.elf'),a.cable)
  deadline=time.monotonic()+30
  while time.monotonic()<deadline:
   raw.extend(uart.read(uart.in_waiting or 1))
   if b'Exit from FSBL' in raw:break
  else:raise RuntimeError('FSBL did not finish')
  run('program',['vivado','-mode','batch','-source',str(REPO/'scripts/program_genesys_pl.tcl'),
                '-tclargs',a.server.removeprefix('tcp:'),a.cable,a.bitstream])
  xs('prepare','diagnostics/drtio/prepare_ps.tcl',a.server,str(ps/'sdt/psu_init.tcl'),a.cable)
  run('phy',['/srv/codex-hil-data/artiq-zynqmp/venv/bin/python',str(REPO/'diagnostics/drtio/test_phy_hw.py'),
             '--server',a.server,'--cable',a.cable,'--csr-map',a.csr_map,'--output',str(out/'phy'),'--cycles','1'])
  if not a.service_elf:
   return 0
  xs('service','scripts/run_ethernet.tcl',a.server,a.service_elf,a.cable)
  deadline=time.monotonic()+10
  while time.monotonic()<deadline:
   raw.extend(uart.read(uart.in_waiting or 1))
   if b'SI_CONTROL_READY 5342' in raw:break
  else:raise RuntimeError('Si5342 service did not start')
 finally:
  uart.close();(out/'uart.log').write_bytes(raw)
 return 0

if __name__=='__main__':raise SystemExit(main())
