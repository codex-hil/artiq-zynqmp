# SPDX-License-Identifier: LGPL-3.0-or-later
"""Exact Xilinx MultiReg logic lowering; reset distribution still functional model."""
import unittest
from types import SimpleNamespace
from migen import Module,ClockDomain,ClockDomainsRenamer,Signal
from migen.sim import run_simulation
from migen.genlib.cdc import MultiReg
from migen.genlib.resetsync import AsyncResetSynchronizer
from migen.build.xilinx.common import XilinxMultiReg
from aux_reset_control import AuxResetControl
from aux_reset_domains import AuxResetDomains
from aux_reset_commands import AuxResetCommands
from master_link_boundary import MasterLinkBoundary
from test_master_ps_cdc import FunctionalReset

class XilinxStartupTests(unittest.TestCase):
    def exercise(self,xilinx):
        d=Module()
        for name in ('management','control','sys','rx'):
            setattr(d.clock_domains,'cd_'+name,ClockDomain(name))
        d.submodules.coordinator=c=ClockDomainsRenamer('control')(AuxResetControl(2))
        d.submodules.domains=r=AuxResetDomains(('sys','rx'),control='control')
        d.submodules.commands=h=AuxResetCommands(c)
        d.comb += [r.request.eq(c.reset),c.domain_ready.eq(r.ready),
                   d.cd_sys.rst.eq(r.reset_out[0]),d.cd_rx.rst.eq(r.reset_out[1])]
        codec=SimpleNamespace(**{n:Signal() for n in
            ('rx_reset','rx_reset_done','rx_clock_active','word_aligned')})
        status=SimpleNamespace(**{n:Signal(reset=1) for n in
            ('reset_done','clock_active','aligned')})
        d.submodules.boundary=b=MasterLinkBoundary(codec,c.admit,c.reset,status)
        def wait(signal,value,limit=100):
            for _ in range(limit):
                if (yield signal)==value:return
                yield
            self.fail('bounded handshake timeout')
        def test():
            # Before the reset status has crossed into management: default and
            # vendor lowering intentionally expose different initialization.
            self.assertEqual((yield h.reset_status),0 if xilinx else 1)
            for _ in range(32):
                self.assertEqual((yield c.admit),0)
                self.assertEqual((yield b.allowed),0)
                self.assertEqual((yield codec.rx_reset),1)
                yield
            self.assertEqual((yield h.reset_status),1)
            self.assertEqual((yield c.request),1)
            yield h.request.eq(0)
            yield h.abandoned.eq(0)
            yield from wait(h.abandonment_ready,1)
            yield h.abandoned.eq(1)
            yield from wait(h.admit,1)
            yield from wait(b.allowed,1)
            # Explicit new reset request eventually closes all admission; no
            # instantaneous cross-domain assertion is claimed by this test.
            yield h.request.eq(1)
            yield from wait(c.reset,1)
            yield from wait(h.reset_status,1)
            yield from wait(b.allowed,0)
            self.assertEqual((yield codec.rx_reset),1)
            self.assertEqual((yield c.admit),0)
            # Stale abandoned=1 is insufficient to release a second episode.
            yield h.request.eq(0)
            for _ in range(24):
                self.assertEqual((yield c.admit),0);yield
            yield h.abandoned.eq(0)
            yield from wait(h.abandonment_ready,1)
            yield h.abandoned.eq(1)
            yield from wait(h.admit,1)
            yield from wait(b.allowed,1)
        overrides={AsyncResetSynchronizer:FunctionalReset}
        if xilinx:overrides[MultiReg]=XilinxMultiReg
        run_simulation(d,{'management':test()},
            clocks={'management':8,'control':10,'sys':14,'rx':18,
                    'aux_release_sys':14,'aux_release_rx':18},special_overrides=overrides)
    def test_default_initialization_and_two_reset_episodes(self):self.exercise(False)
    def test_exact_xilinx_initialization_and_two_reset_episodes(self):self.exercise(True)
if __name__=='__main__':unittest.main()
