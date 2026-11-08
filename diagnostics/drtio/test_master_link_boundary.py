# SPDX-License-Identifier: LGPL-3.0-or-later
import unittest
from types import SimpleNamespace
from migen import Module,Signal,ClockDomain
from migen.sim import run_simulation
from raw20_codec import Raw20Codec
from master_link_boundary import MasterLinkBoundary

class LinkBoundaryTests(unittest.TestCase):
    def test_restart_before_admission_and_status_losses(self):
        d=Module();d.clock_domains.cd_sys=ClockDomain('sys')
        admit=Signal();request=Signal(reset=1)
        status=SimpleNamespace(reset_done=Signal(),clock_active=Signal(),aligned=Signal())
        d.submodules.codec=codec=Raw20Codec()
        d.submodules.boundary=b=MasterLinkBoundary(codec,admit,request,status)
        def test():
            for _ in range(6):yield
            self.assertEqual((yield codec.channel.rx_ready),0)
            self.assertEqual((yield b.gt_reset_request),1)
            yield request.eq(0)
            for signal in (status.reset_done,status.clock_active,status.aligned):yield signal.eq(1)
            for _ in range(6):yield
            # GT reset released so clocks may restart, but traffic still blocked.
            self.assertEqual((yield b.gt_reset_request),0)
            self.assertEqual((yield codec.channel.rx_ready),0)
            yield admit.eq(1)
            for _ in range(6):yield
            self.assertEqual((yield codec.channel.rx_ready),1)
            for signal in (status.reset_done,status.clock_active,status.aligned):
                yield signal.eq(0)
                for _ in range(6):yield
                self.assertEqual((yield codec.channel.rx_ready),0)
                yield signal.eq(1)
                for _ in range(6):yield
                self.assertEqual((yield codec.channel.rx_ready),1)
            yield request.eq(1)
            for _ in range(6):yield
            self.assertEqual((yield b.gt_reset_request),1)
            self.assertEqual((yield codec.channel.rx_ready),0)
            yield d.cd_sys.rst.eq(1)
            for _ in range(4):yield
            yield d.cd_sys.rst.eq(0)
            yield admit.eq(0)
            yield request.eq(0)
            for _ in range(6):yield
            self.assertEqual((yield codec.channel.rx_ready),0)
        run_simulation(d,test(),clocks={'sys':14,'rtio_rx':18})

if __name__=='__main__':unittest.main()
