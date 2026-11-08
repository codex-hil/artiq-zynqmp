# SPDX-License-Identifier: LGPL-3.0-or-later
"""Native encoded link admission loss/restart, no physical GT/clock stop."""
import unittest
from unittest.mock import patch
from types import SimpleNamespace
from migen import Module,Signal,ClockDomainsRenamer,ClockDomain
from migen.sim import run_simulation
from raw20_codec import Raw20Codec
from protocol_probe import WordAligner
from master_link_boundary import MasterLinkBoundary
from master_aux import GenesysMasterAux
from aux_controller_gray import GrayAuxController
from test_master_routing import Pair,CLOCKS

class BoundaryPair(Module):
    def __init__(self,nwords):
        if nwords!=2:raise ValueError('raw20 only')
        self.submodules.a=Raw20Codec();self.submodules.b=Raw20Codec()
        self.submodules.align_a=ClockDomainsRenamer('rtio_rx')(WordAligner())
        self.submodules.align_b=ClockDomainsRenamer('rtio_rx')(WordAligner())
        self.alice,self.bob=self.a.channel,self.b.channel
        self.comb += [self.align_a.input.eq(self.b.tx_raw),self.align_b.input.eq(self.a.tx_raw),
            self.a.rx_raw.eq(self.align_a.output),self.b.rx_raw.eq(self.align_b.output),
            self.b.rx_reset_done.eq(1),self.b.rx_clock_active.eq(1),
            self.b.word_aligned.eq(self.align_b.aligned)]

class RelockTests(unittest.TestCase):
    def test_native_link_down_blocked_and_fresh_aux_recovery(self):
        with patch('test_master_routing.EncodedPair',BoundaryPair):d=Pair()
        d.clock_domains.cd_sys=ClockDomain('sys')
        d.submodules.aux=GenesysMasterAux(d.master,controller_type=GrayAuxController)
        d.submodules.peer=GrayAuxController(d.satellite.link_layer)
        admit=Signal();request=Signal(reset=1)
        status=SimpleNamespace(reset_done=Signal(reset=1),clock_active=Signal(reset=1),aligned=d.wires.align_a.aligned)
        d.submodules.boundary=MasterLinkBoundary(d.wires.a,admit,request,status)
        def wait(csr,value):
            for _ in range(1200):
                if bool((yield from csr.read()))==value:return
                yield
            self.fail('Native link state timeout')
        def exchange(index):
            words=[0x12345678+index,0xabcdef00+index]
            for j,word in enumerate(words):yield from d.aux.bus.write(j,word)
            yield from d.aux.controller.transmitter.aux_tx_length.write(8)
            yield from d.aux.controller.transmitter.aux_tx.write(1)
            yield from wait(d.peer.receiver.aux_rx_present,True)
            self.assertEqual((yield from d.peer.receiver.aux_read_pointer.read()),index)
            actual=[]
            for j in range(2):actual.append((yield from d.peer.bus.read(2048+index*256+j)))
            self.assertEqual(actual,words)
            self.assertEqual((yield from d.peer.receiver.aux_rx_error.read()),0)
            yield from d.peer.receiver.aux_rx_present.write(1)
            for _ in range(16):yield
        def test():
            yield request.eq(0);yield admit.eq(1)
            yield from wait(d.master.link_layer.rx_up,True)
            yield from wait(d.satellite.link_layer.rx_up,True)
            yield from exchange(0)
            yield admit.eq(0);yield request.eq(1)
            yield status.reset_done.eq(0);yield status.clock_active.eq(0)
            yield from wait(d.master.link_layer.rx_up,False)
            for _ in range(24):yield
            self.assertEqual((yield d.wires.a.channel.rx_ready),0)
            yield request.eq(0)
            yield status.reset_done.eq(1);yield status.clock_active.eq(1)
            for _ in range(64):
                self.assertEqual((yield d.master.link_layer.rx_up.status),0)
                yield
            yield admit.eq(1)
            yield from wait(d.master.link_layer.rx_up,True)
            yield from wait(d.satellite.link_layer.rx_up,True)
            yield from exchange(1)
            self.assertEqual((yield d.master.rt_controller.csrs.protocol_error.w),0)
        run_simulation(d,test(),CLOCKS)

if __name__=='__main__':unittest.main()
