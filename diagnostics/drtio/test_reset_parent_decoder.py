# SPDX-License-Identifier: LGPL-3.0-or-later
"""Characterize decoder lock: PASS reproduces management write blocking."""
import unittest
from migen import Module
from migen.sim import run_simulation
from litex.soc.interconnect.axi import AXIInterface,AXIDecoder

class ParentDecoderTests(unittest.TestCase):
    def test_unaccepted_target_b_blocks_management_aw(self):
        d=Module()
        make=lambda:AXIInterface(data_width=32,address_width=40,id_width=16)
        host,target,management=make(),make(),make()
        split=0xa0020000//4
        d.submodules.decoder=AXIDecoder(host,
            [(lambda a:a<split,target),(lambda a:a>=split,management)])
        def test():
            yield target.aw.ready.eq(1)
            yield target.w.ready.eq(1)
            yield management.aw.ready.eq(1)
            yield management.ar.ready.eq(1)
            yield host.aw.addr.eq(0xa0002000)
            yield host.aw.valid.eq(1)
            yield
            self.assertEqual((yield host.aw.ready),1)
            yield host.aw.valid.eq(0)
            for _ in range(3):yield
            yield host.aw.addr.eq(0xa0020004)
            yield host.aw.valid.eq(1)
            yield
            # A missing B retains write selection on target indefinitely.
            for _ in range(20):
                self.assertEqual((yield host.aw.ready),0)
                self.assertEqual((yield management.aw.valid),0)
                yield
            # Independent read direction can still select management status.
            yield host.ar.addr.eq(0xa0020008)
            yield host.ar.valid.eq(1)
            yield
            self.assertEqual((yield host.ar.ready),1)
            self.assertEqual((yield management.ar.valid),1)
            yield
            yield host.ar.valid.eq(0)
            # Only a real target completion releases the write-direction lock.
            yield target.b.valid.eq(1)
            yield host.b.ready.eq(1)
            yield
            yield target.b.valid.eq(0)
            for _ in range(3):yield
            self.assertEqual((yield host.aw.ready),1)
            self.assertEqual((yield management.aw.valid),1)
        run_simulation(d,test())

if __name__=='__main__':unittest.main()
