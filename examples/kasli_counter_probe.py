"""Kasli local RTIO counter and synchronous RPC probe; no TTL writes.

LGPL-3.0-or-later.
"""
from artiq.experiment import *
from artiq.coredevice.core import Core
from numpy import int64


@compile
class KasliCounterProbe(EnvExperiment):
    core: KernelInvariant[Core]

    def build(self):
        self.setattr_device('core')

    @rpc
    def report(self, before: int64, after: int64) -> int64:
        if before <= 0 or after - before < 1000000:
            raise ValueError('RTIO counter failed to advance by requested 1ms')
        print('KASLI_COUNTER_RPC_PASS', before, after, flush=True)
        return int64(0x12345678)

    @kernel
    def run(self):
        self.core.reset()
        before = self.core.get_rtio_counter_mu()
        self.core.delay(0.001)
        self.core.wait_until_mu(now_mu())
        after = self.core.get_rtio_counter_mu()
        assert self.report(before, after) == int64(0x12345678)
