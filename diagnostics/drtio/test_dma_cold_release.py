"""No-TSC admission fault must allow actual AUX/SED cold release; LGPL-3.0-or-later."""
import unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"boards/genesys_zu-5ev/1_gateware"))
from migen import Module,ClockDomain,Signal
from migen.sim import run_simulation
from migen.genlib.resetsync import AsyncResetSynchronizer
from litex.soc.interconnect.axi import AXIInterface
from aux_ps import AuxPS
from dma_csr import DMACSR
from test_aux_ps import FunctionalReset
from test_dma_csr import CSRDriver

class ColdReleaseTests(unittest.TestCase):
    def test_idle_fault_rejects_start_without_holding_sed_in_reset(self):
        d=Module();d.clock_domains.cd_rtio_rx=ClockDomain('rtio_rx')
        bus=AXIInterface(data_width=64,address_width=49,id_width=6)
        d.submodules.control=c=DMACSR(bus)
        d.submodules.ps=p=AuxPS(extra_banks=[('dma',4,c.csrs)],output_pad=Signal(),
            dma_cri=c.cri,dma_rtio_reset=c.rtio_reset_request,dma_owner=Signal())
        driver=CSRDriver(self,p.axi,c.memory_map(p.BASE+4*0x800)['registers'])
        def run():
            # Remote TSC is absent until firmware enables TX after cold release.
            yield c.fault.eq(1);yield p.reset.eq(0)
            for _ in range(30):yield
            self.assertEqual((yield p.rtio_reset_applied.status),1)
            self.assertEqual((yield p.phy_reset_applied.status),1)
            yield p.phy_reset_request.storage_full.eq(0)
            for _ in range(20):yield
            self.assertEqual((yield p.phy_reset_applied.status),0)
            yield p.rtio_reset_request.storage_full.eq(0)
            for _ in range(30):yield
            self.assertEqual((yield c.rtio_reset_request),0)
            self.assertEqual((yield p.rtio_reset_applied.status),0)
            yield from driver.write('address',0x22000000)
            yield from driver.write('max_bursts',16)
            yield from driver.write('watchdog',1000)
            yield from driver.write('start',1)
            self.assertEqual((yield from driver.read('reject')),32)
            self.assertEqual((yield from driver.read('accepted')),0)
            self.assertEqual((yield from driver.read('active')),0)
            self.assertEqual((yield bus.ar.valid),0)
            self.assertEqual((yield p.rtio_reset_applied.status),0)
        run_simulation(d,{'sys':run()},clocks={'sys':10,'gth_tx':8,'gth_rx':8,
            'aux_sys':10,'aux_tx':8,'aux_rx':8,'rtio_rx':8,'dma_write':10,'dma_read':8},
            special_overrides={AsyncResetSynchronizer:FunctionalReset})

if __name__=='__main__':unittest.main()
