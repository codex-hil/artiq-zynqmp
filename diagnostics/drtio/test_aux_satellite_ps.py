"""Raw20 TSC loads, real AXI CSR reads and common reset; LGPL-3.0-or-later."""
import unittest
from types import SimpleNamespace
from migen import Module, Signal, ClockDomainsRenamer
from migen.sim import run_simulation, passive
from migen.genlib.resetsync import AsyncResetSynchronizer
from artiq.gateware.drtio.link_layer import LinkLayerTX
from artiq.gateware.drtio.rt_packet_master import RTPacketMaster
from aux_ps import AuxPS
from raw20_codec import Raw20Codec
from test_aux_ps import FunctionalReset


class AuxSatellitePSTests(unittest.TestCase):
    def test_real_raw20_tsc_load_counter_axi_and_reset_epoch(self):
        d=Module()
        d.submodules.ps=p=AuxPS(output_pad=Signal(),input_pad=Signal())
        d.submodules.source=codec=ClockDomainsRenamer('gth_rx')(Raw20Codec(rx_domain='gth_tx'))
        d.submodules.tx=tx=ClockDomainsRenamer('gth_rx')(LinkLayerTX(codec.encoder))
        link=SimpleNamespace(tx_rt_frame=tx.rt_frame,tx_rt_data=tx.rt_data,
            rx_rt_frame=Signal(),rx_rt_data=Signal(16))
        d.submodules.master=m=ClockDomainsRenamer({'sys':'gth_rx','rtio_rx':'gth_tx'})(RTPacketMaster(link))
        d.comb += p.rx_raw.eq(codec.tx_raw)
        regs=p.memory_map()['registers'];a=p.axi
        requests=[0]
        @passive
        def source():
            sent=0
            while True:
                if requests[0]>sent:
                    yield m.tsc_value.eq(requests[0]*1000)
                    yield m.set_time_stb.eq(1)
                    for _ in range(100):
                        yield
                        if (yield m.set_time_ack):break
                    else:self.fail('TSC packet TX timeout')
                    yield m.set_time_stb.eq(0)
                    sent+=1
                yield
        def wait(signal):
            for _ in range(100):
                if (yield signal):return
                yield
            self.fail('AXI timeout')
        def read(name):
            yield a.ar.addr.eq(regs[name]['address'])
            yield a.ar.id.eq(3);yield a.ar.len.eq(0)
            yield a.ar.size.eq(2);yield a.ar.burst.eq(1)
            yield a.ar.valid.eq(1)
            yield from wait(a.ar.ready)
            yield
            yield a.ar.valid.eq(0)
            yield from wait(a.r.valid)
            self.assertEqual((yield a.r.resp),0)
            self.assertEqual((yield a.r.id),3)
            value=(yield a.r.data)
            yield a.r.ready.eq(1)
            yield
            yield a.r.ready.eq(0)
            yield
            return value
        def write(name,value):
            yield a.aw.addr.eq(regs[name]['address'])
            yield a.aw.id.eq(5);yield a.aw.len.eq(0)
            yield a.aw.size.eq(2);yield a.aw.burst.eq(1)
            yield a.aw.valid.eq(1)
            yield from wait(a.aw.ready)
            yield
            yield a.aw.valid.eq(0)
            yield a.w.data.eq(value);yield a.w.strb.eq(15)
            yield a.w.last.eq(1);yield a.w.valid.eq(1)
            yield from wait(a.w.ready)
            yield
            yield a.w.valid.eq(0)
            yield from wait(a.b.valid)
            self.assertEqual((yield a.b.resp),0)
            yield a.b.ready.eq(1)
            yield
            yield a.b.ready.eq(0)
            yield
        def run():
            yield p.reset.eq(1)
            for _ in range(10):yield
            yield p.reset.eq(0)
            for _ in range(200):yield
            self.assertEqual((yield from read('rx_up')),1)
            self.assertEqual((yield from read('tsc_load_count')),0)
            for epoch in (1,2):
                requests[0]=epoch
                for _ in range(100):yield
                self.assertEqual((yield from read('tsc_load_count')),1)
                self.assertGreaterEqual((yield p.satellite.backend.tsc.coarse_ts),epoch*1000)
                self.assertEqual((yield from read('rt_reply_fault')),0)
                self.assertEqual((yield from read('rtio_error_flags')),0)
                self.assertEqual((yield from read('rtio_reset_applied')),1)
                self.assertEqual((yield from read('phy_reset_applied')),1)
                yield from write('phy_reset_request',0)
                for _ in range(20):yield
                self.assertEqual((yield from read('phy_reset_applied')),0)
                # Release the cold/common-reset hold, then command a new
                # datapath reset solely through actual PS AXI CSR writes.
                yield from write('rtio_reset_request',0)
                for _ in range(20):yield
                self.assertEqual((yield from read('rtio_reset_applied')),0)
                before=(yield p.satellite.backend.tsc.coarse_ts)
                yield from write('rtio_reset_request',1)
                for _ in range(20):yield
                self.assertEqual((yield from read('rtio_reset_applied')),1)
                self.assertGreater((yield p.satellite.backend.tsc.coarse_ts),before)
                self.assertEqual((yield from read('tsc_load_count')),1)
                yield from write('rtio_reset_request',0)
                for _ in range(20):yield
                self.assertEqual((yield from read('rtio_reset_applied')),0)
                self.assertEqual((yield from read('tsc_load_count')),1)
                yield from write('phy_reset_request',1)
                for _ in range(20):yield
                self.assertEqual((yield from read('phy_reset_applied')),1)
                self.assertEqual((yield from read('tsc_load_count')),1)
                # Return the hold for the next common-reset epoch.
                yield from write('rtio_reset_request',1)
                yield p.reset.eq(1)
                for _ in range(10):yield
                self.assertEqual((yield from read('tsc_load_count')),0)
                yield p.reset.eq(0)
                for _ in range(200):yield
                self.assertEqual((yield from read('rx_up')),1)
                self.assertEqual((yield from read('tsc_load_count')),0)
        run_simulation(d,{'sys':run(),'gth_rx':source()},
            clocks={'sys':13,'gth_rx':8,'gth_tx':(11,3),
                    'aux_sys':13,'aux_rx':8,'aux_tx':(11,3)},
            special_overrides={AsyncResetSynchronizer:FunctionalReset})
