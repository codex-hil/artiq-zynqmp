#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Exact LiteX common-reset FIFO fixture, no production changes."""
import sys
from pathlib import Path
from migen import Module,ClockDomain,Signal
from migen.fhdl import verilog
from migen.build.xilinx.common import xilinx_special_overrides
from litex.soc.interconnect.stream import ClockDomainCrossing
m=Module();ios=set()
for name in ('ps','tx'):
 cd=ClockDomain(name);setattr(m.clock_domains,'cd_'+name,cd)
 cd.clk.name_override=name+'_clock';cd.rst.name_override=name+'_reset';ios.update((cd.clk,cd.rst))
m.submodules.fifo=f=ClockDomainCrossing([('data',32)],cd_from='ps',cd_to='tx',depth=4,with_common_rst=True)
for prefix,endpoint in (('sink',f.sink),('source',f.source)):
 for name in ('valid','ready','data'):
  s=getattr(endpoint,name);s.name_override=prefix+'_'+name;ios.add(s)
for i,cd in enumerate(f._fragment.clock_domains):
 s=Signal(name_override='private_reset'+str(i));m.comb+=s.eq(cd.rst);ios.add(s)
result=verilog.convert(m,ios=ios,name='csr_fifo_reset',special_overrides=xilinx_special_overrides)
result.write(sys.argv[1])

p=Path(sys.argv[1]);p.write_text("`timescale 1ns/1ps\n"+p.read_text())
