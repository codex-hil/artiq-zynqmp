#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Separate five-domain masked-ready candidate; no production assembly changes."""
import sys
from pathlib import Path
from migen import Module,Signal,ClockDomain,ClockDomainsRenamer
from migen.build.xilinx.common import xilinx_special_overrides
from migen.fhdl import verilog
from aux_reset_control import AuxResetControl
from aux_reset_domains_masked import AuxResetDomainsMasked
from aux_reset_commands import AuxResetCommands
m=Module();ios=set();domains=('ps','sys','rtio_rx','rio','rio_phy')
clocks={name:Signal(name_override=name+'_clock') for name in ('management','control','ps','tx','rx')}
ios.update(clocks.values())
for name in ('management','control')+domains:
 cd=ClockDomain(name);setattr(m.clock_domains,'cd_'+name,cd)
 clock=clocks['tx' if name in ('sys','rio','rio_phy') else 'rx' if name=='rtio_rx' else name]
 m.comb+=cd.clk.eq(clock)
m.submodules.coordinator=c=ClockDomainsRenamer('control')(AuxResetControl(5))
m.submodules.releases=r=AuxResetDomainsMasked(domains,control='control')
m.submodules.commands=h=AuxResetCommands(c)
m.comb += [r.request.eq(c.reset),c.domain_ready.eq(r.ready)]
for i,name in enumerate(domains):m.comb+=getattr(m,'cd_'+name).rst.eq(r.reset_out[i])
for name,signal in {'request':h.request,'abandoned':h.abandoned,'admit':h.admit,
 'abandon_ready':h.abandonment_ready,'reset_status':h.reset_status,
 'domain_ready':r.ready,'target_reset':r.reset_out,'coordinator_reset':c.reset}.items():
 signal.name_override=name;ios.add(signal)
verilog.convert(m,ios=ios,name='reset_five_domains',special_overrides=xilinx_special_overrides).write(sys.argv[1])
p=Path(sys.argv[1]);p.write_text('`timescale 1ns/1ps\n'+p.read_text())
