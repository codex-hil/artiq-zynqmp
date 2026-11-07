"""Native local/remote RTIO routing tests; LGPL-3.0-or-later.

Ideal clocks/raw20 only; explicit owner selection is not a DMA engine test.
"""
import unittest
from migen import Module, Signal, passive
from migen.sim import run_simulation
from artiq.gateware import rtio
from artiq.gateware.rtio import cri
from artiq.gateware.rtio.phy import ttl_simple
from artiq.gateware.drtio.core import DRTIOSatellite, SyncRTIO
from artiq.gateware.test.drtio.test_full_stack import DummyRXSynchronizer
from artiq.coredevice.exceptions import RTIODestinationUnreachable, RTIOUnderflow
from master_backend import GenesysMasterBackend
from master_routing import GenesysMasterRouting
from test_packets_raw20 import EncodedPair

CLOCKS={'sys':8,'rtio_rx':8,'rio':8,'rio_phy':8}

class Pair(Module):
    def __init__(self):
        self.local_pad=Signal();self.remote_pad=Signal()
        self.submodules.wires=EncodedPair(2)
        self.submodules.time=rtio.TSC(glbl_fine_ts_width=3)
        self.submodules.remote_time=rtio.TSC(glbl_fine_ts_width=3)
        self.submodules.master=GenesysMasterBackend(self.time,self.wires.alice)
        self.submodules.ki=rtio.KernelInitiator(self.time)
        self.submodules.local_phy=ttl_simple.Output(self.local_pad)
        self.submodules.remote_phy=ttl_simple.Output(self.remote_pad)
        # Upstream latency RAM requires at least two channels in this fixture.
        self.submodules.local_spare=ttl_simple.Output(Signal())
        self.submodules.remote_spare=ttl_simple.Output(Signal())
        self.submodules.local=SyncRTIO(self.time,[rtio.Channel.from_phy(self.local_phy),rtio.Channel.from_phy(self.local_spare)],lane_count=4,fifo_depth=8)
        self.submodules.satellite=DRTIOSatellite(self.remote_time,self.wires.bob,DummyRXSynchronizer())
        for csr in [self.satellite.reset,self.satellite.reset_phy]:
            csr.storage.reset=0;csr.storage_full.reset=0
        self.submodules.remote_io=SyncRTIO(self.remote_time,[rtio.Channel.from_phy(self.remote_phy),rtio.Channel.from_phy(self.remote_spare)],lane_count=4,fifo_depth=8)
        self.comb += [self.satellite.cri.connect(self.remote_io.cri),self.satellite.async_errors.eq(self.remote_io.async_errors)]
        self.submodules.routing=GenesysMasterRouting([self.ki.cri],self.local.cri,self.master.cri)

class MasterRoutingTests(unittest.TestCase):
    def exercise(self,unknown=False,early=False):
        d=Pair();edges=[];done=[False]
        def write(channel,timestamp,value):
            yield from d.ki.target.write(channel<<8)
            yield from d.ki.now_hi.write(timestamp>>32)
            yield from d.ki.now_lo.write(timestamp&0xffffffff)
            # Native SED requires timestamp/channel in cycle1, command in cycle2.
            # now_lo is a synchronous CSR; allow its committed value to stage.
            if not early:yield
            yield from d.ki.o_data.write(value)
            yield
            for _ in range(200):
                status=yield from d.ki.o_status.read()
                if status&4:raise RTIODestinationUnreachable
                if status&2:raise RTIOUnderflow
                if status==0:return
                yield
            self.fail('Kernel request did not finish')
        def run():
            c=d.master.rt_controller.csrs
            yield from c.underflow_margin.write(100)
            for _ in range(500):
                if (yield from d.master.link_layer.rx_up.read()):break
                yield
            else:self.fail('Encoded link not up')
            yield from c.o_get_buffer_space.write(1)
            for _ in range(500):
                yield
                if not (yield from c.o_wait.read()):break
            else:self.fail('Remote buffer request timeout')
            base=((yield d.time.full_ts_cri)+4096)&~7
            if early:
                with self.assertRaises(RTIOUnderflow):
                    yield from write(0,base,1)
            elif unknown:
                with self.assertRaises(RTIODestinationUnreachable):
                    yield from write(255<<16,base,1)
            else:
                for offset,node,value in [(0,0,1),(160,0,0),(320,1,1),(480,1,0)]:
                    yield from write(node<<16,base+offset,value)
            for _ in range(800):yield
            self.assertEqual((yield d.local.async_errors.raw_bits()),0)
            self.assertEqual((yield d.remote_io.async_errors.raw_bits()),0)
            done[0]=True
        @passive
        def monitor():
            previous=[0,0];cycle=0
            while True:
                current=[(yield d.local_pad),(yield d.remote_pad)]
                for i in range(2):
                    if current[i]!=previous[i]:edges.append((cycle,i,current[i]))
                previous=current;cycle+=1;yield
        def watchdog():
            for _ in range(3500):
                if done[0]:return
                yield
            self.fail('Routing test timeout')
        run_simulation(d,{'sys':[run(),monitor(),watchdog()]},CLOCKS)
        if unknown or early:self.assertEqual(edges,[])
        else:
            self.assertEqual([(node,value) for _,node,value in edges],[(0,1),(0,0),(1,1),(1,0)])
            self.assertEqual(edges[1][0]-edges[0][0],20)
            self.assertEqual(edges[3][0]-edges[2][0],20)
    def test_local_and_remote_outputs_are_separate(self):self.exercise()
    def test_unmapped_node_has_no_local_or_remote_edge(self):self.exercise(True)
    def test_unstaged_timestamp_is_refused_without_edge(self):self.exercise(early=True)
    def test_two_explicit_owners_gate_commands(self):
        d=Module();a,b,local,remote=[cri.Interface() for _ in range(4)]
        d.submodules.route=GenesysMasterRouting([a,b],local,remote)
        def run():
            yield a.chan_sel.eq(0);yield b.chan_sel.eq(1<<16)
            yield a.cmd.eq(cri.commands['write']);yield b.cmd.eq(cri.commands['write'])
            for _ in range(4):yield
            self.assertEqual((yield local.cmd),cri.commands['write']);self.assertEqual((yield remote.cmd),0)
            yield a.cmd.eq(0);yield b.cmd.eq(0)
            for _ in range(3):yield
            yield from d.route.owner.write(1)
            for _ in range(4):yield
            yield a.cmd.eq(cri.commands['write']);yield b.cmd.eq(cri.commands['write'])
            for _ in range(4):yield
            self.assertEqual((yield local.cmd),0);self.assertEqual((yield remote.cmd),cri.commands['write'])
        run_simulation(d,run())

if __name__=='__main__':unittest.main()
