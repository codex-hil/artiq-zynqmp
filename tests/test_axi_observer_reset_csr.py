"""Lost history and read-only CSR controls; LGPL-3.0-or-later."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'diagnostics/ddr'))
from migen import Module,ResetInserter,run_simulation,passive
from misoc.interconnect.csr import CSRStatus
from litex.soc.interconnect.axi import AXIInterface
from axi_read_observer_csr import AXIReadObserverCSR

class Tests(unittest.TestCase):
 def test_reset_loses_count_but_never_qualifies_drain(self):
  top=Module();b=AXIInterface(data_width=64,address_width=49,id_width=6)
  top.submodules.monitor=ResetInserter()(AXIReadObserverCSR(b));m=top.monitor
  external={'accepted':0,'returned':0}
  @passive
  def scoreboard():
   while True:
    if (yield b.ar.valid) and (yield b.ar.ready):external['accepted']+=1
    if (yield b.r.valid) and (yield b.r.ready) and (yield b.r.last):external['returned']+=1
    yield
  def run():
   yield b.ar.valid.eq(1);yield b.ar.ready.eq(1)
   yield;yield
   yield b.ar.valid.eq(0);yield
   self.assertEqual((yield m.outstanding.status),external['accepted'])
   self.assertGreater(external['accepted'],0)
   yield m.reset.eq(1);yield;yield
   yield m.reset.eq(0);yield;yield
   self.assertGreater(external['accepted']-external['returned'],0)
   self.assertEqual((yield m.outstanding.status),0)  # History lost, not drained.
   self.assertEqual((yield m.flags.status),0)  # quiet/epoch bits remain0.
   yield b.r.valid.eq(1);yield b.r.ready.eq(1);yield b.r.last.eq(1)
   yield;yield
   yield b.r.valid.eq(0);yield;yield
   self.assertEqual((yield m.flags.status)&1,1)  # unmatched reply after reset
   self.assertEqual((yield m.flags.status)&12,0)
  run_simulation(top,[run(),scoreboard()])
 def test_status_csrs_only_and_no_bus_driving(self):
  b=AXIInterface(data_width=64,address_width=49,id_width=6)
  m=AXIReadObserverCSR(b)
  self.assertEqual([c.name for c in m.get_csrs()],['outstanding','flags'])
  self.assertTrue(all(isinstance(c,CSRStatus) for c in m.get_csrs()))
  # Inspect generated RTL: the observer has only input-facing AXI signals.
  from migen.fhdl import verilog
  rtl=str(verilog.convert(m,ios={b.ar.valid,b.ar.ready,b.r.valid,b.r.ready,b.r.last,b.r.resp}))
  for line in rtl.splitlines():
   if 'input' in line:continue
   self.assertFalse('output' in line and ('ar_' in line or 'r_' in line),line)
if __name__=='__main__':unittest.main()
