"""PS CSR -> one-shot read delay -> native SED underflow; LGPL-3.0-or-later.

RTL only, scaled timing and functional resets. No A53 firmware/AUX/master.
"""
import sys,unittest
from pathlib import Path
from migen import Module,Signal,ClockDomain,ClockDomainsRenamer,passive
from migen.sim import run_simulation
from migen.genlib.resetsync import AsyncResetSynchronizer
from litex.soc.interconnect.axi import AXIInterface
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tests'))
sys.path.insert(0,str(ROOT/'boards/genesys_zu-5ev/1_gateware'))
from test_zynqmp_dma import AXIMemorySim,encode_sequence
from test_aux_ps import FunctionalReset
from test_dma_csr import CSRDriver
from test_satellite_sed import interface
from aux_ps import AuxPS
from satellite_backend import SatelliteBackend
from dma_read_delay_control import LabDelayedDMACSR


class DelayCSRSEDTests(unittest.TestCase):
    def test_csr_armed_fault_snapshot_clear_and_unarmed_positive(self):
        d=Module();d.clock_domains.cd_rtio_rx=ClockDomain('rtio_rx')
        bus=AXIInterface(data_width=64,address_width=49,id_width=6)
        # Scale clock metadata to keep simulation short: 1600 sys cycles.
        # Physical timing must be chosen separately from the actual PS clock.
        d.submodules.control=c=LabDelayedDMACSR(bus,sys_clk_hz=800000,
                                                arena_base=0,arena_size=4096)
        d.submodules.ps=p=AuxPS(extra_banks=[('dma',4,c.csrs)])
        pad=Signal()
        d.submodules.backend=b=ClockDomainsRenamer('rtio_rx')(
            SatelliteBackend(interface(),pad,glbl_fine_ts_width=3,dma_cri=c.cri))
        d.comb += b.rtio_reset.eq(c.rtio_reset_request)
        driver=CSRDriver(self,p.axi,c.memory_map(p.BASE+4*0x800)['registers'])
        trace=encode_sequence([(0,0,0,1),(0,256,0,0)],8)
        memory=AXIMemorySim(bus,trace,max_queue=3)
        ar=[];last=[];held=[];edges=[];writes=[]
        @passive
        def monitor():
            while True:
                if (yield bus.ar.valid) and (yield bus.ar.ready):ar.append((yield bus.ar.addr))
                if (yield bus.r.valid) and (yield bus.r.ready) and (yield bus.r.last):last.append(1)
                if (yield c.read_delay.holding) and (yield c.engine.active) and ar:
                    held.append(1)
                    self.assertFalse(last)
                    self.assertFalse(writes)
                yield
        @passive
        def rx():
            old=0
            while True:
                if (yield c.cri.cmd)==1:writes.append((yield c.cri.o_timestamp))
                value=(yield pad)
                if value!=old:edges.append(((yield b.tsc.coarse_ts),value));old=value
                yield
        def pending():
            for _ in range(400):
                if (yield from driver.read('pending')):return
            self.fail('No CSR completion within bound')
        def run():
            yield c.fault.eq(0);yield b.cri_switch.selected.storage.eq(1)
            yield from driver.write('address',0)
            yield from driver.write('max_bursts',16)
            yield from driver.write('watchdog',20000)
            self.assertEqual((yield from driver.read('lab_delay_cycles')),1600)
            yield from driver.write('lab_delay_arm',1)
            self.assertEqual((yield from driver.read('lab_delay_armed')),1)
            target=(yield b.tsc.coarse_ts)+800
            yield from driver.write('time_offset',target<<3)
            self.assertLess((yield b.tsc.coarse_ts),target)
            yield from driver.write('start',1)
            yield from pending()
            self.assertTrue(held)
            self.assertEqual((yield from driver.read('accepted')),1)
            self.assertEqual((yield from driver.read('completed')),1)
            self.assertEqual((yield from driver.read('result_error')),4)
            self.assertEqual((yield from driver.read('result_channel')),0)
            self.assertEqual((yield from driver.read('result_timestamp')),target<<3)
            self.assertEqual((yield from driver.read('lab_delay_triggers')),1)
            self.assertEqual((yield from driver.read('lab_delay_armed')),0)
            self.assertEqual((yield from driver.read('lab_delay_holding')),0)
            self.assertEqual(len(ar),len(last));self.assertFalse(memory.queue)
            self.assertFalse(edges)
            # Pending result owns the slot: an unacknowledged restart is denied.
            count=len(ar)
            yield from driver.write('start',1)
            self.assertTrue((yield from driver.read('reject'))&64)
            self.assertEqual((yield from driver.read('accepted')),1)
            self.assertEqual((yield from driver.read('result_timestamp')),target<<3)
            self.assertEqual(len(ar),count)
            yield from driver.write('clear',1)
            self.assertEqual((yield from driver.read('pending')),0)
            # Explicit CSR-level reuse tests the peripheral, not firmware recovery.
            target=(yield b.tsc.coarse_ts)+1000
            yield from driver.write('time_offset',target<<3)
            yield from driver.write('start',1)
            yield from pending()
            self.assertEqual((yield from driver.read('result_error')),0)
            self.assertEqual((yield from driver.read('accepted')),2)
            self.assertEqual((yield from driver.read('completed')),2)
            self.assertEqual((yield from driver.read('lab_delay_triggers')),1)
            self.assertEqual((yield from driver.read('lab_delay_rejected')),0)
            self.assertEqual(len(ar),len(last));self.assertFalse(memory.queue)
            while (yield b.tsc.coarse_ts)<target+100:yield
            self.assertEqual(edges,[(target+11,1),(target+43,0)])
        run_simulation(d,{'sys':[run(),monitor(),memory.ar(),memory.r()],'rtio_rx':rx()},
                       clocks={'sys':10,'rtio_rx':(8,1),'dma_write':10,'dma_read':(8,1),
                               'gth_rx':8,'gth_tx':(11,3),'aux_sys':10,'aux_rx':8,'aux_tx':(11,3)},
                       special_overrides={AsyncResetSynchronizer:FunctionalReset})
