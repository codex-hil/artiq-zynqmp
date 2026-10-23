"""Negative ownership proof: PL reset need not drain PS AXI. LGPL-3.0-or-later."""
import unittest
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"diagnostics/ddr"))
from axi_read_observer import AXIReadObserver
from migen import Module, ResetInserter, passive, run_simulation
from litex.soc.interconnect.axi import AXIInterface
from test_zynqmp_dma import dma

COUNTEREXAMPLE={}


class ResetOwnershipTests(unittest.TestCase):
 def test_isolated_logic_reset_can_hide_pending_axi(self):
  top=Module();bus=AXIInterface(data_width=64,address_width=49,id_width=6)
  top.submodules.dut=ResetInserter()(dma.DMA(bus));dut=top.dut
  top.submodules.observer=AXIReadObserver(bus)
  accepted=[]
  @passive
  def monitor():
   while True:
    if (yield bus.ar.valid) and (yield bus.ar.ready):accepted.append((yield bus.ar.addr))
    yield
  def stimulus():
   yield top.observer.epoch_qualified.eq(1)
   yield bus.ar.ready.eq(1)
   yield bus.r.valid.eq(0)  # Legal delayed PS response remains outstanding.
   yield from dut.enable.write(1)
   for _ in range(50):
    if accepted:break
    yield
   else:self.fail('No accepted burst before reset')
   yield bus.ar.ready.eq(0)
   yield dut.reset.eq(1)   # Model PL logic reset only; do not reset AXI owner.
   for _ in range(4):yield
   idle=(yield dut.enable.w)==0
   self.assertTrue(idle)
   self.assertGreater(len(accepted),0)
   self.assertEqual((yield top.observer.outstanding),len(accepted))
   self.assertEqual((yield top.observer.quiet),0)
   COUNTEREXAMPLE.update(observer_outstanding=(yield top.observer.outstanding),observer_quiet=(yield top.observer.quiet),idle=idle,accepted_bursts=len(accepted),returned_bursts=0,
                        isolated_pl_reset=True,ps_transaction_owner_reset=False,
                        conclusion='IDLE alone is not quiescence after independent PL reset')
  run_simulation(top,[stimulus(),monitor()])


if __name__=='__main__':unittest.main()
