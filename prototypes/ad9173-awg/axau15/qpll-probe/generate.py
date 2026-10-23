"""Generate only the pinned LiteICLink QPLL common; no transceiver channels."""
import json
from pathlib import Path
from migen import Module, Signal, ClockDomain
from migen.fhdl import verilog
from liteiclink.serdes.gth4_ultrascale import GTH4QuadPLL
m = Module()
m.clock_domains.cd_sys = ClockDomain('sys', reset_less=True)
ref = Signal(name='refclk')
rst = Signal(name='reset')
lock = Signal(name='locked')
m.submodules.qpll = q = GTH4QuadPLL(ref, 245.76e6, 6.144e9)
m.comb += [q.reset.eq(rst), q.powerdown.eq(0), lock.eq(q.lock),
           q.drp.clk.eq(m.cd_sys.clk), q.drp.addr.eq(0), q.drp.di.eq(0),
           q.drp.en.eq(0), q.drp.we.eq(0)]
verilog.convert(m, ios={ref, rst, lock, m.cd_sys.clk}, name='qpll_common').write('qpll_common.v')
Path('qpll.json').write_text(json.dumps(q.config, indent=2)+'\n')
