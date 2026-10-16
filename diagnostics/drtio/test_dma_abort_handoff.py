"""Actual DMA abort -> native packet/SED handoff, RTL only; LGPL-3.0-or-later."""
import sys,unittest
from pathlib import Path
from migen import Module,Signal,ClockDomain,ClockDomainsRenamer,passive
from migen.genlib.cdc import MultiReg
from migen.genlib.resetsync import AsyncResetSynchronizer
from migen.sim.core import Simulator
from litex.soc.interconnect.axi import AXIInterface
from artiq.gateware.drtio.rt_packet_master import RTPacketMaster
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tests'))
sys.path.insert(0,str(ROOT/'boards/genesys_zu-5ev/1_gateware'))
from test_zynqmp_dma import AXIMemorySim,encode_sequence
from test_aux_ps import FunctionalReset
from test_satellite_sed import interface
from satellite_backend import SatelliteBackend
from dma_async_engine import AsyncSatelliteDMA
from satellite_dma_probe import abort_trace_bytes


class HandoffTests(unittest.TestCase):
    def exercise(self,pause=False,saturated=False):
        d=Module();d.clock_domains.cd_rtio_rx=ClockDomain('rtio_rx')
        bus=AXIInterface(data_width=64,address_width=49,id_width=6)
        d.submodules.engine=e=AsyncSatelliteDMA(bus)
        pad=Signal();sl,ml=interface(),interface()
        d.submodules.backend=b=ClockDomainsRenamer('rtio_rx')(SatelliteBackend(sl,pad,glbl_fine_ts_width=3,dma_cri=e.cri))
        d.submodules.master=m=ClockDomainsRenamer({'sys':'rtio_rx','rtio_rx':'rtio_rx'})(RTPacketMaster(ml))
        owner=Signal();d.specials += MultiReg(e.active | e.recovering,owner,'rtio_rx')
        d.comb += [b.cri_switch.selected.storage.eq(owner),b.rtio_reset.eq(e.rtio_reset_request),
            sl.rx_rt_frame.eq(ml.tx_rt_frame),sl.rx_rt_data.eq(ml.tx_rt_data),
            ml.rx_rt_frame.eq(sl.tx_rt_frame),ml.rx_rt_data.eq(sl.tx_rt_data)]
        trace=encode_sequence([(0,1200<<3,0,1),(0,2000<<3,0,0)],8)
        if saturated:
            data=abort_trace_bytes()
            trace=[int.from_bytes(data[i:i+8],'big') for i in range(0,len(data),8)]
        memory=AXIMemorySim(bus,trace+[0]*512,max_queue=70)
        writes=[];ar=[];rlast=[];requests=[];edges=[];sim_box=[]
        @passive
        def rx():
            old=0;previous_time=None
            while True:
                now=(yield b.tsc.coarse_ts)
                if previous_time is not None:self.assertEqual(now,previous_time+1)
                previous_time=now
                if (yield e.cri.cmd)==1:writes.append(1)
                value=(yield pad)
                if value!=old:edges.append(((yield b.tsc.coarse_ts),value));old=value
                if requests and (yield m.sr_ack):
                    ts,v=requests.pop(0)
                    yield m.sr_timestamp.eq(ts<<3);yield m.sr_data.eq(v);yield m.sr_stb.eq(1)
                else:yield m.sr_stb.eq(0)
                yield
        @passive
        def monitor():
            while True:
                if (yield bus.ar.valid) and (yield bus.ar.ready):ar.append(1)
                if (yield bus.r.valid) and (yield bus.r.ready) and (yield bus.r.last):rlast.append(1)
                yield
        def run():
            yield e.max_bursts.eq(256 if saturated else 16)
            for _ in range(30):yield
            yield e.start.eq(1);yield;yield e.start.eq(0)
            stalled=0
            for _ in range(10000 if saturated else 1000):
                if saturated:
                    stalled=stalled+1 if (yield e.cri.o_status)&1 else 0
                    if stalled>=32:break
                elif len(writes)>=2:break
                yield
            else:self.fail('DMA did not reach required admission/backpressure')
            self.assertEqual((yield e.active),1)
            if saturated:
                self.assertGreater(len(writes),2)
                self.assertLess(len(writes),1100)
                self.assertEqual((yield e.error),0)
                self.assertEqual((yield e.budget_error),0)
                self.assertFalse(edges)
                print('SATURATED_DMA_BEFORE_ABORT writes=%d ar=%d rlast=%d' %
                      (len(writes),len(ar),len(rlast)),flush=True)
            if pause:
                for name in ('rtio_rx','dma_read'):
                    sim_box[0].time.clocks[name].time_before_trans=10**9
            yield e.abort.eq(1);yield;yield e.abort.eq(0)
            for _ in range(2000):
                if (yield e.done):break
                yield
            else:self.fail('Abort did not drain')
            if pause:
                for _ in range(3):yield
                self.assertEqual((yield e.recovering),1)
                count=len(ar)
                yield e.start.eq(1);yield;yield e.start.eq(0)
                for _ in range(5):yield
                self.assertEqual((yield e.rejected_start),1)
                self.assertEqual(len(ar),count)
                for name in ('rtio_rx','dma_read'):
                    clock=sim_box[0].time.clocks[name];clock.time_before_trans=clock.half_period
            for _ in range(50):yield
            self.assertEqual(len(ar),len(rlast))
            self.assertLessEqual(len(ar),256 if saturated else 16)
            self.assertEqual((yield e.active),0)
            self.assertEqual((yield e.recovering),0)
            self.assertEqual((yield e.error)&1,1) # preserve sticky diagnostics
            if saturated:
                self.assertEqual((yield e.error),1)
                self.assertEqual((yield e.budget_error),0)
                self.assertEqual((yield e.guard.outstanding),0)
                print('SATURATED_DMA_AFTER_ABORT ar=%d rlast=%d error=1 outstanding=0' %
                      (len(ar),len(rlast)),flush=True)
            self.assertEqual((yield b.phy_reset),0)
            self.assertEqual((yield b.rtio_reset),0)
            self.assertEqual((yield owner),0)
            # Wait beyond both canceled DMA timestamps. No new DMA start clears
            # the error; the packet engine must become usable independently.
            if not saturated:
                while (yield b.tsc.coarse_ts)<2200:yield
            self.assertFalse(edges)
            target=(yield b.tsc.coarse_ts)+300
            requests.extend([(target,1),(target+100,0)])
            while (yield b.tsc.coarse_ts)<target+200:yield
            self.assertEqual(edges,[(target+11,1),(target+111,0)])
            self.assertEqual((yield b.async_errors.raw_bits()),0)
        with Simulator(d,{'sys':[run(),monitor(),memory.ar(),memory.r()],'rtio_rx':rx()},
            clocks={'sys':10,'rtio_rx':(13,2),'dma_write':10,'dma_read':(13,2)},
            special_overrides={AsyncResetSynchronizer:FunctionalReset}) as sim:
            sim_box.append(sim);sim.run()

    def test_abort_drain_then_native_packet_without_new_dma(self):self.exercise()

    def test_rx_clock_pause_abort_then_packet_without_new_dma(self):self.exercise(pause=True)

    def test_long_fixture_actual_sed_backpressure_abort_and_packet(self):
        # Proves actual backpressure/drain/handoff, not absence of all future
        # edges at the fixture's distant timestamps (physical test still due).
        self.exercise(saturated=True)
