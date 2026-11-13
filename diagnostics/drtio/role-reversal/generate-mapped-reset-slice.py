#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Reconstruct audited primitive slice; raw coordinator D is a test boundary."""
import argparse,json,hashlib
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('capture',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
cells={};pins={};params={}
for line in a.capture.read_text().splitlines():
 f=line.split('\t')
 if f[0]=='CELL':cells[f[1]]=(f[2],f[3]);pins[f[1]]={};params[f[1]]={}
 elif f[0]=='PIN':
  cell,pin=f[1].rsplit('/',1);assert f[3] and ',' not in f[3];pins[cell][pin]=(f[2],f[3])
 elif f[0]=='PARAM':params[f[1]][f[2]]=f[3]
assert sorted(ref for ref,init in cells.values())==['FDPE']*4+['FDSE','GND','LUT1','LUT2','VCC']
external={'pl_clk0':'pl_clock','mastergthadapter_tx_clock':'tx_clock','pl_resetn0':'pl_resetn','genesysmasterintegration_ingress_raw_reset':'raw_reset'}
drivers={}
for cell,cpins in pins.items():
 for pin,(direction,net) in cpins.items():
  if direction=='OUT':assert net not in drivers;drivers[net]=(cell,pin)
assert {net for cpins in pins.values() for direction,net in cpins.values() if direction=='IN' and net not in drivers}==set(external)
nets=sorted(drivers);mapping={**external,**{n:'n'+str(i) for i,n in enumerate(nets)}}
coord='genesysmasterintegration_ingress_outputs_reset_reg';assert cells[coord]==('FDSE',"1'b1")
assert cells[drivers[pins[coord]['CE'][1]][0]][0]=='VCC'
assert cells[drivers[pins['FDPE_4']['D'][1]][0]][0]=='GND'
s='`timescale 1ns/1ps\nmodule mapped_reset #(parameter MUTATE_CE=0,MUTATE_AND=0,MUTATE_HANDOVER=0,MUTATE_SET=0)(input pl_clock,tx_clock,pl_resetn,raw_reset,handover_fault,output control_reset,coordinator_reset,retained_request,sys_reset);\n'
s+='wire '+','.join(mapping[n] for n in nets)+';\n'
for index,(cell,(ref,init)) in enumerate(cells.items()):
 par=[]
 if init:par.append('.INIT('+('MUTATE_AND ? 4\'h8 : '+init if ref=='LUT2' else init)+')')
 for name,value in params[cell].items():
  if value:par.append('.'+name+'('+value+')')
 ports=[]
 for pin,(direction,net) in pins[cell].items():
  value=mapping[net]
  if cell==coord and pin=='CE':value="(MUTATE_CE || (MUTATE_HANDOVER && handover_fault)) ? 1'b0 : "+value
  if cell==coord and pin=='S':value="(MUTATE_SET && handover_fault) ? 1'b0 : "+value
  ports.append('.'+pin+'('+value+')')
 s+=ref+(' #('+','.join(par)+')' if par else '')+' cell'+str(index)+'('+','.join(ports)+');\n'
for out,cell in [('control_reset','FDPE_5'),('coordinator_reset',coord),('sys_reset','FDPE_29')]:s+='assign '+out+'='+mapping[pins[cell]['Q'][1]]+';\n'
s+='assign retained_request='+mapping[pins['FDPE_28']['PRE'][1]]+';\nendmodule\n'
a.output.mkdir(parents=True,exist_ok=True);(a.output/'mapped_reset.v').write_text(s)
(a.output/'slice-binding.json').write_text(json.dumps({'status':'CLOSED_PRIMITIVE_SLICE_GENERATED','capture_sha256':hashlib.sha256(a.capture.read_bytes()).hexdigest(),'cells':cells,'params':params,'pins':pins,'external_boundary':external,'limits':['raw coordinator D supplied externally, no FSM/GT/AXI','Empty inversion parameters retain vendor library defaults','No SDF or routed delays']},indent=2)+'\n')
