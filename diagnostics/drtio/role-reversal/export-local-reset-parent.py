#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Isolated exact parent reset wiring; clocks/GT/AXI not a full board model."""
import sys
from pathlib import Path
from types import SimpleNamespace
from migen import Module,Signal,ClockDomain,ClockDomainsRenamer
from migen.genlib.resetsync import AsyncResetSynchronizer
from migen.build.xilinx.common import xilinx_special_overrides
from migen.fhdl import verilog
from aux_reset_control import AuxResetControl
from aux_reset_registered import AuxResetRegistered
from aux_reset_domains_grouped import AuxResetDomainsGrouped
from master_admission_registered import MasterAdmissionRegistered
from master_link_local_reset import MasterLinkLocalReset
m=Module();ios=set();clocks={n:Signal(name_override=n+'_clock') for n in ('pl','tx','rx')};ios.update(clocks.values())
pl_resetn=Signal(name_override='pl_resetn');ios.add(pl_resetn)
for name in ('control','ps','sys','rtio_rx','rio','rio_phy'):
 cd=ClockDomain(name);setattr(m.clock_domains,'cd_'+name,cd)
 m.comb+=cd.clk.eq(clocks['pl' if name in ('control','ps') else 'rx' if name=='rtio_rx' else 'tx'])
m.specials+=AsyncResetSynchronizer(m.cd_control,~pl_resetn)
m.submodules.coordinator=c=ClockDomainsRenamer('control')(AuxResetControl(5))
m.submodules.registered=o=AuxResetRegistered(c)
m.submodules.releases=r=AuxResetDomainsGrouped(shared_tx_clock_confirmed=True,shared_reset_policy_confirmed=True)
if '--retain-control-reset' in sys.argv:
 from aux_reset_retention import AuxResetRetention
 m.submodules.retention=hold=AuxResetRetention(o.reset,m.cd_control.rst)
 release_request=hold.request
else:release_request=o.reset
m.comb += [r.request.eq(release_request),c.domain_ready.eq(r.ready)]
for i,name in enumerate(('ps','sys','rtio_rx','rio','rio_phy')):
 m.comb+=getattr(m,'cd_'+name).rst.eq(r.reset_out[i] | ~pl_resetn)
m.submodules.sample=s=MasterAdmissionRegistered(o.admit,o.reset)
codec=SimpleNamespace(**{n:Signal(name_override='codec_'+n) for n in ('rx_reset','rx_reset_done','rx_clock_active','word_aligned')})
status=SimpleNamespace(**{n:Signal(reset=1,name_override='status_'+n) for n in ('reset_done','clock_active','aligned')})
m.submodules.boundary=b=MasterLinkLocalReset(codec,s.allowed,o.reset,status,parent_reset_contract_confirmed=True)
for name,signal in {'request':c.request,'abandoned':c.requester_abandoned,'abandon_ready':o.abandonment_ready,'allowed':b.allowed,'domain_ready':r.ready,'target_reset':r.reset_out,'control_reset':m.cd_control.rst,'sys_reset':m.cd_sys.rst,'coordinator_reset':o.reset}.items():
 signal.name_override=name;ios.add(signal)
p=Path(sys.argv[1]);verilog.convert(m,ios=ios,name='local_reset_parent',special_overrides=xilinx_special_overrides).write(str(p));p.write_text('`timescale 1ns/1ps\n'+p.read_text())
