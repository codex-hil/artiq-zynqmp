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
from aux_reset_domains import AuxResetDomains
from aux_reset_commands import AuxResetCommands
m=Module();ios=set();source_clocks={};domains=('ps','sys','rtio_rx','rio','rio_phy')
clocks={name:Signal(name_override=name+'_clock') for name in ('management','control','ps','tx','rx')}
ios.update(clocks.values())
for name in ('management','control')+domains:
 cd=ClockDomain(name);setattr(m.clock_domains,'cd_'+name,cd)
 clock=clocks['tx' if name in ('sys','rio','rio_phy') else 'rx' if name=='rtio_rx' else name]
 m.comb+=cd.clk.eq(clock);source_clocks[name]=clock
m.submodules.coordinator=c=ClockDomainsRenamer('control')(AuxResetControl(5))
release_type=AuxResetDomains if '--original' in sys.argv else AuxResetDomainsMasked
if '--grouped-tx' in sys.argv:
 if '--original' in sys.argv or '--registered-outputs' not in sys.argv:
  raise ValueError('Grouped candidate requires registered outputs and masked ready')
 from aux_reset_domains_grouped import AuxResetDomainsGrouped
 common=source_clocks['sys'] is source_clocks['rio'] is source_clocks['rio_phy']
 m.submodules.releases=r=AuxResetDomainsGrouped(shared_tx_clock_confirmed=common,
     shared_reset_policy_confirmed=True)
else:m.submodules.releases=r=release_type(domains,control='control')
if '--registered-outputs' in sys.argv:
 from aux_reset_registered import AuxResetRegistered
 m.submodules.registered=external=AuxResetRegistered(c)
else:external=c
m.submodules.commands=h=AuxResetCommands(external)
m.comb += [r.request.eq(external.reset),c.domain_ready.eq(r.ready)]
for i,name in enumerate(domains):m.comb+=getattr(m,'cd_'+name).rst.eq(r.reset_out[i])
for name,signal in {'request':h.request,'abandoned':h.abandoned,'admit':h.admit,
 'abandon_ready':h.abandonment_ready,'reset_status':h.reset_status,
 'domain_ready':r.ready,'target_reset':r.reset_out,'coordinator_reset':external.reset}.items():
 signal.name_override=name;ios.add(signal)
verilog.convert(m,ios=ios,name='reset_five_domains',special_overrides=xilinx_special_overrides).write(sys.argv[1])
p=Path(sys.argv[1]);p.write_text('`timescale 1ns/1ps\n'+p.read_text())
