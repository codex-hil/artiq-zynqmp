"""Host AXI writes cannot arm diagnostic observer; LGPL-3.0-or-later."""
import sys,unittest
from pathlib import Path
from migen import Signal,run_simulation
from litex.soc.interconnect.axi import AXIInterface
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'boards/genesys_zu-5ev/1_gateware'))
from local_rtio import LocalRTIO
from test_local_rtio import AXIMaster

class Tests(unittest.TestCase):
 def test_real_axi_csr_writes_do_not_arm_or_change_counter(self):
  bus=AXIInterface(data_width=64,address_width=49,id_width=6)
  dut=LocalRTIO(Signal(),Signal(),bus,analyzer=True,dma_observer=True)
  host=AXIMaster(dut.axi)
  def run():
   self.assertEqual((yield from host.read(0xa0003000)),0)
   self.assertEqual((yield from host.read(0xa0003004)),0)
   yield from host.write(0xa0003000,0xffffffff)
   yield from host.write(0xa0003004,0xffffffff)
   self.assertEqual((yield from host.read(0xa0003000)),0)
   self.assertEqual((yield from host.read(0xa0003004)),0)
   self.assertEqual((yield dut.dma_observer.observer.epoch_qualified),0)
   self.assertEqual((yield dut.dma_observer.observer.quiet),0)
  run_simulation(dut,run())

if __name__=='__main__':unittest.main()
