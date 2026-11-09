#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Exact existing Xilinx async reset lowering, no replacement model."""
import sys
from pathlib import Path
from migen import Module,Signal,ClockDomain
from migen.genlib.resetsync import AsyncResetSynchronizer
from migen.build.xilinx.common import xilinx_special_overrides
from migen.fhdl import verilog
m=Module();m.clock_domains.cd_rx=ClockDomain('rx')
source=Signal(name_override='source_clk');request=Signal(name_override='reset_request')
m.cd_rx.rst.name_override='reset_out'
m.comb+=m.cd_rx.clk.eq(source)
m.specials+=AsyncResetSynchronizer(m.cd_rx,request)
verilog.convert(m,ios={source,request,m.cd_rx.rst},name='reset_sync',
 special_overrides=xilinx_special_overrides).write(sys.argv[1])
# Simulation unit metadata only; exact vendor-generated logic above is unchanged.
output=Path(sys.argv[1]);output.write_text('`timescale 1ns/1ps\n'+output.read_text())
