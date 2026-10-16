"""Native AXI DMA and serialized RT packets share actual satellite SED/TTL.

LGPL-3.0-or-later. Ideal synchronous AXI memory and packet wires only; no PS
CDC, firmware DDMA trace handling, or live ownership changes are qualified.
"""
import sys
from pathlib import Path
import unittest
from migen import Module,Signal,ClockDomainsRenamer,passive
from migen.sim import run_simulation
from litex.soc.interconnect.axi import AXIInterface
from artiq.gateware.drtio.rt_packet_master import RTPacketMaster
from satellite_backend import SatelliteBackend
from test_satellite_sed import interface

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'boards/genesys_zu-5ev/1_gateware'))
sys.path.insert(0,str(ROOT/'tests'))
from test_zynqmp_dma import AXIMemorySim,encode_sequence

class SatelliteDMATests(unittest.TestCase):
    def exercise(self,underflow=False):
        dut=Module();pad=Signal()
        bus=AXIInterface(data_width=64,address_width=49,id_width=6)
        fine=3
        base=10 if underflow else 1200
        writes=[(0,(base+i*32)<<fine,0,1-i%2) for i in range(4)]
        # Second aligned trace always valid; used after an explicit error clear.
        first=encode_sequence(writes,8)
        second=encode_sequence([(0,(i*32)<<fine,0,1-i%2) for i in range(4)],8)
        memory=AXIMemorySim(bus,first+[0]*(64-len(first))+second)
        ml,sl=interface(),interface()
        dut.submodules.backend=b=SatelliteBackend(sl,pad,glbl_fine_ts_width=fine,dma_membus=bus)
        dut.submodules.master=m=ClockDomainsRenamer({'rtio_rx':'sys'})(RTPacketMaster(ml))
        dut.comb += [sl.rx_rt_frame.eq(ml.tx_rt_frame),sl.rx_rt_data.eq(ml.tx_rt_data),
                     ml.rx_rt_frame.eq(sl.tx_rt_frame),ml.rx_rt_data.eq(sl.tx_rt_data)]
        edges=[];commands=[];loads=[];errors=[];drain_waits=[]
        @passive
        def monitor():
            old=0
            while True:
                ts=(yield b.tsc.coarse_ts);value=(yield pad)
                if value!=old:edges.append((ts,value));old=value
                if (yield b.dma.cri.cmd)==1:commands.append((yield b.dma.cri.o_timestamp))
                if (yield b.packet.tsc_load):loads.append((yield b.packet.tsc_load_value))
                errors.append((yield b.async_errors.raw_bits()))
                yield
        def bounded_wait_idle():
            for cycles in range(1500):
                if not (yield b.dma.enable.w):
                    self.assertEqual(memory.queue,[])
                    drain_waits.append(cycles)
                    return
                yield
            self.fail('DMA did not drain/finish within bound')
        def stimulus():
            for _ in range(20):yield
            # Default owner0: real serialized writes execute normally.
            yield m.sr_timestamp.eq(200<<fine);yield m.sr_data.eq(1);yield m.sr_stb.eq(1)
            yield
            while not (yield m.sr_ack):yield
            yield m.sr_stb.eq(0)
            for _ in range(220):yield
            # Same native CRISwitch used by upstream satman; change only idle.
            yield from b.cri_switch.selected.write(1)
            yield from b.dma.dma.base_address.write(0)
            yield from b.dma.enable.write(1)
            yield
            yield from bounded_wait_idle()
            self.assertEqual((yield b.dma.dma.wb_reader.bus_error.status),0)
            self.assertEqual((yield b.dma.cri_master.error.w),1 if underflow else 0)
            if underflow:
                yield from b.dma.cri_master.error.write(1)
            yield from b.cri_switch.selected.write(0)
            # Wait past first trace's physical events, then prove packet owner
            # returns by a serialized low transition on the actual TTL.
            while (yield b.tsc.coarse_ts)<2000:yield
            yield m.sr_timestamp.eq(2200<<fine);yield m.sr_data.eq(0);yield m.sr_stb.eq(1)
            yield
            while not (yield m.sr_ack):yield
            yield m.sr_stb.eq(0)
            while (yield b.tsc.coarse_ts)<3000:yield
            yield from b.cri_switch.selected.write(1)
            yield from b.dma.time_offset.time_offset.write(3200<<fine)
            yield from b.dma.dma.base_address.write(512)
            yield from b.dma.enable.write(1)
            yield
            yield from bounded_wait_idle()
            self.assertEqual((yield b.dma.cri_master.error.w),0)
            yield from b.cri_switch.selected.write(0)
            while (yield b.tsc.coarse_ts)<3400:yield
        run_simulation(dut,[stimulus(),monitor(),memory.ar(),memory.r()])
        expected=[(211,1)]
        if not underflow:expected += [(1211,1),(1243,0),(1275,1),(1307,0)]
        # First DMA high overlaps the prior packet high, so it has no edge.
        if not underflow:expected.remove((1211,1))
        else:expected += [(2211,0)]
        expected += [(3211,1),(3243,0),(3275,1),(3307,0)]
        self.assertEqual(edges,expected)
        self.assertFalse(any(errors))
        self.assertFalse(loads)
        self.assertEqual(commands,([10<<fine] if underflow else [(1200+i*32)<<fine for i in range(4)])+
                         [(3200+i*32)<<fine for i in range(4)])
        print('DMA_DRAIN_WAIT_CYCLES',underflow,drain_waits)
    def test_native_dma_packet_handoff_and_reuse(self):self.exercise()
    def test_underflow_no_future_phantom_and_recovery(self):self.exercise(underflow=True)
