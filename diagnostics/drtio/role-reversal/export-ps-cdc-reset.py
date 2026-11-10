#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Exact five-channel PSCDC fixture with all endpoint metadata exposed."""
import sys,json
from pathlib import Path
from migen import Module,ClockDomain,Signal,Cat
from migen.fhdl import verilog
from migen.build.xilinx.common import xilinx_special_overrides
from litex.soc.interconnect.axi import AXILiteInterface
from master_ps_cdc import GenesysMasterPSCDC
m=Module();ios=set()
for name in ('ps','tx'):
 cd=ClockDomain(name);setattr(m.clock_domains,'cd_'+name,cd)
 cd.clk.name_override=name+'_clock';cd.rst.name_override=name+'_reset';ios.update((cd.clk,cd.rst))
ps=AXILiteInterface(data_width=32,address_width=40);tx=AXILiteInterface(data_width=32,address_width=40)
m.submodules.cdc=c=GenesysMasterPSCDC(ps,tx,ps_clock='ps',master_clock='tx')
widths={}
for name in ('aw','w','b','ar','r'):
 src,dst=(getattr(tx,name),getattr(ps,name)) if name in ('b','r') else (getattr(ps,name),getattr(tx,name))
 def packed(e):
  fields=[e.first,e.last,e.payload.raw_bits(),e.param.raw_bits()]
  return Cat(*(field for field in fields if len(field)))
 width=len(packed(src));widths[name]=width
 incoming=Signal(width,name_override=name+'_input');outgoing=Signal(width,name_override=name+'_output')
 m.comb += [packed(src).eq(incoming),outgoing.eq(packed(dst))];ios.update((incoming,outgoing))
 for e,prefix in ((src,'sink'),(dst,'source')):
  for field in ('valid','ready'):
   s=getattr(e,field);s.name_override=name+'_'+prefix+'_'+field;ios.add(s)
resets=Signal(10,name_override='private_resets');ios.add(resets)
for i,f in enumerate(c.crossings.values()):
 for j,cd in enumerate(f._fragment.clock_domains):m.comb+=resets[2*i+j].eq(cd.rst)
out=Path(sys.argv[1]);out.mkdir(exist_ok=True)
r=verilog.convert(m,ios=ios,name='ps_cdc_reset',special_overrides=xilinx_special_overrides)
r.write(str(out/'ps_cdc_reset.v'));p=out/'ps_cdc_reset.v';p.write_text('`timescale 1ns/1ps\n'+p.read_text())
(out/'widths.json').write_text(json.dumps(widths,indent=2)+'\n')
