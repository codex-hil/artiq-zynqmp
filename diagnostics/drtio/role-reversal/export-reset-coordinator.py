#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Isolated original reset coordinator/commands/domain release digital assembly."""
import sys
from pathlib import Path
from migen import Module,Signal,ClockDomain,ClockDomainsRenamer
from migen.genlib.resetsync import AsyncResetSynchronizer
from migen.build.xilinx.common import xilinx_special_overrides
from migen.fhdl import verilog
from aux_reset_control import AuxResetControl
from aux_reset_domains import AuxResetDomains
from aux_reset_commands import AuxResetCommands
m=Module();ios=set()
for name in ('management','control','a','b'):
 cd=ClockDomain(name);setattr(m.clock_domains,'cd_'+name,cd)
 clock=Signal(name_override=name+'_clock');m.comb+=cd.clk.eq(clock);ios.add(clock)
m.submodules.coordinator=c=ClockDomainsRenamer('control')(AuxResetControl(2))
m.submodules.releases=r=AuxResetDomains(('a','b'),control='control')
m.submodules.commands=h=AuxResetCommands(c)
m.comb += [r.request.eq(c.reset),c.domain_ready.eq(r.ready),
           m.cd_a.rst.eq(r.reset_out[0]),m.cd_b.rst.eq(r.reset_out[1])]
for name,signal in {'request':h.request,'abandoned':h.abandoned,'admit':h.admit,
 'abandon_ready':h.abandonment_ready,'reset_status':h.reset_status,
 'domain_ready':r.ready,'target_reset':r.reset_out}.items():
 signal.name_override=name;ios.add(signal)
result=verilog.convert(m,ios=ios,name='reset_coordinator',special_overrides=xilinx_special_overrides)
result.write(sys.argv[1]);p=Path(sys.argv[1]);p.write_text('`timescale 1ns/1ps\n'+p.read_text())
