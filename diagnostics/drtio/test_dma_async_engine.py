"""Actual AXI -> async raw queue -> native DMA/CRI -> SED/TTL; LGPL-3.0-or-later.

RTL only with functional reset model. No hardware timing/DDR qualification.
"""
import sys
from pathlib import Path
from types import SimpleNamespace
import unittest
from migen import Module,Signal,ClockDomain,ClockDomainsRenamer,passive
from migen.sim.core import Simulator
from migen.genlib.resetsync import AsyncResetSynchronizer
from litex.soc.interconnect.axi import AXIInterface
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'boards/genesys_zu-5ev/1_gateware'))
sys.path.insert(0,str(ROOT/'tests'))
from test_zynqmp_dma import AXIMemorySim,encode_sequence
from test_aux_ps import FunctionalReset
from dma_async_engine import AsyncSatelliteDMA
from satellite_backend import SatelliteBackend
from test_satellite_sed import interface

class AsyncDMAEngineTests(unittest.TestCase):
    def exercise(self,underflow=False,pause=False,response=0,rx_period=(8,1),delayed_read=False):
        d=Module();d.clock_domains.cd_rtio_rx=ClockDomain('rtio_rx')
        bus=AXIInterface(data_width=64,address_width=49,id_width=6)
        d.submodules.engine=e=AsyncSatelliteDMA(bus)
        pad=Signal();link=interface()
        d.submodules.backend=b=ClockDomainsRenamer('rtio_rx')(
            SatelliteBackend(link,pad,glbl_fine_ts_width=3,dma_cri=e.cri))
        d.comb += b.rtio_reset.eq(e.rtio_reset_request)
        first=encode_sequence([(0,(10+i*32 if underflow else 1200+i*32)<<3,0,1-i%2) for i in range(4)],8)
        second=encode_sequence([(0,i*32<<3,0,1-i%2) for i in range(4)],8)
        memory=AXIMemorySim(bus,first+[0]*(64-len(first))+second,max_queue=3)
        memory.response=response
        edges=[];requests=[];last=[];rx_ticks=[];sim_box=[];cri_writes=[]
        @passive
        def rx():
            old=0
            while True:
                rx_ticks.append(1)
                if (yield e.cri.cmd)==1:cri_writes.append((yield e.cri.o_timestamp))
                value=(yield pad)
                if value!=old:edges.append(((yield b.tsc.coarse_ts),value));old=value
                yield
        @passive
        def axi_monitor():
            while True:
                if (yield bus.ar.valid) and (yield bus.ar.ready):requests.append((yield bus.ar.addr))
                if (yield bus.r.valid) and (yield bus.r.ready) and (yield bus.r.last):last.append(1)
                yield
        @passive
        def delayed_memory():
            # Keep AXI RVALID low while AR transactions remain outstanding.
            # The trace is future-dated at start; live TSC passes it before
            # any payload arrives. No CRI status/error register is injected.
            while (yield b.tsc.coarse_ts)<1500:yield
            self.assertEqual((yield e.active),1)
            self.assertTrue(requests)
            self.assertFalse(last)
            self.assertFalse(cri_writes)
            yield from memory.r()
        def done():
            for _ in range(4000):
                if (yield e.done):return
                yield
            self.fail('Async DMA did not complete/drain within bound')
        def run():
            yield b.cri_switch.selected.storage.eq(1)
            for _ in range(30):yield
            if delayed_read:self.assertLess((yield b.tsc.coarse_ts),1200)
            yield e.address.eq(0);yield e.start.eq(1);yield;yield e.start.eq(0)
            if pause:
                # First admit actual future SED events, then stop RX before
                # their timestamps. Abort must clear them, not just the decoder.
                for _ in range(1000):
                    if len(cri_writes)>=2:break
                    yield
                else:self.fail('No CRI events before forced clock loss')
                for _ in range(10):yield
                for name in ('rtio_rx','dma_read'):
                    sim_box[0].time.clocks[name].time_before_trans=10**9
                ticks=len(rx_ticks)
                yield e.abort.eq(1)
            yield from done()
            self.assertEqual((yield e.error),1 if pause else 4 if underflow or delayed_read else 2 if response else 0)
            self.assertEqual(len(requests),len(last))
            self.assertFalse(memory.queue)
            if pause:
                self.assertEqual(len(rx_ticks),ticks)
                self.assertFalse(edges)
                for name in ('rtio_rx','dma_read'):
                    c=sim_box[0].time.clocks[name];c.time_before_trans=c.half_period
            if underflow or delayed_read:
                self.assertEqual((yield e.error_timestamp),(10 if underflow else 1200)<<3)
                self.assertEqual((yield e.error_channel),0)
            yield e.abort.eq(0)
            for _ in range(5):yield
            while (yield b.tsc.coarse_ts)<1600:yield
            baseline=list(edges)
            memory.response=0
            # Fresh relative trace with a latched nonzero offset.
            target=(yield b.tsc.coarse_ts)+1000
            yield e.address.eq(512);yield e.time_offset.eq(target<<3)
            yield e.start.eq(1);yield;yield e.start.eq(0)
            yield from done()
            self.assertEqual((yield e.error),0)
            self.assertEqual(len(requests),len(last))
            while (yield b.tsc.coarse_ts)<target+200:yield
            self.assertEqual(edges[len(baseline):],[(target+11+i*32,1-i%2) for i in range(4)])
            self.assertEqual((yield b.async_errors.raw_bits()),0)
            if not (underflow or pause or delayed_read):self.assertEqual(baseline,[(1211+i*32,1-i%2) for i in range(4)])
            else:self.assertFalse(baseline)
        with Simulator(d,{'sys':[run(),axi_monitor(),memory.ar(),delayed_memory() if delayed_read else memory.r()],'rtio_rx':rx()},
            clocks={'sys':10,'rtio_rx':rx_period,'dma_write':10,'dma_read':rx_period},
            special_overrides={AsyncResetSynchronizer:FunctionalReset}) as sim:
            sim_box.append(sim);sim.run()
    def test_async_native_decoder_cri_ttl_and_next_trace(self):self.exercise(rx_period=(13,2))
    def test_native_underflow_snapshot_and_recovery(self):self.exercise(underflow=True)
    def test_future_trace_expires_during_active_axi_read(self):self.exercise(delayed_read=True)
    def test_clock_pause_abort_drain_and_recovery(self):self.exercise(pause=True)
    def test_axi_error_report_and_next_trace(self):self.exercise(response=2)


class AsyncDMAAdmissionTests(unittest.TestCase):
    def exercise(self,busy=False):
        d=Module();d.clock_domains.cd_rtio_rx=ClockDomain('rtio_rx')
        bus=AXIInterface(data_width=64,address_width=49,id_width=6)
        d.submodules.engine=e=AsyncSatelliteDMA(bus)
        words=encode_sequence([(0,100000,0,1)]*8,8)
        memory=AXIMemorySim(bus,words,max_queue=3)
        ar=[];rlast=[]
        @passive
        def monitor():
            while True:
                if (yield bus.ar.valid) and (yield bus.ar.ready):ar.append((yield bus.ar.addr))
                if (yield bus.r.valid) and (yield bus.r.ready) and (yield bus.r.last):rlast.append(1)
                yield
        def wait_done():
            for _ in range(2000):
                if (yield e.done):return
                yield
            self.fail('Admission/abort failed to finish')
        def run():
            yield e.cri.o_status.eq(1)
            yield e.address.eq(0 if busy else 64)
            yield e.start.eq(1);yield;yield e.start.eq(0)
            if busy:
                for _ in range(100):yield
                self.assertEqual((yield e.active),1)
                yield e.address.eq(1024);yield e.start.eq(1);yield;yield e.start.eq(0);yield
                self.assertEqual((yield e.rejected_start),1)
                self.assertEqual((yield e.guard.reader.base_address.storage),0)
                yield e.abort.eq(1)
            yield from wait_done()
            self.assertEqual((yield e.error),1 if busy else 16)
            self.assertEqual(len(ar),len(rlast))
            if not busy:self.assertFalse(ar)
            yield
        with Simulator(d,{'sys':[run(),monitor(),memory.ar(),memory.r()]},
            clocks={'sys':10,'rtio_rx':(13,2),'dma_write':10,'dma_read':(13,2)},
            special_overrides={AsyncResetSynchronizer:FunctionalReset}) as sim:sim.run()
    def test_unaligned_trace_rejected_before_axi(self):self.exercise()
    def test_busy_start_rejected_and_original_epoch_drains(self):self.exercise(busy=True)

    def test_unsupported_memory_width_rejected(self):
        with self.assertRaises(ValueError):
            AsyncSatelliteDMA(AXIInterface(data_width=32,address_width=49,id_width=6))
