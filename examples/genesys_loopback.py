"""Physical JB1→JB2 loopback. Prepared only; run after fitting the jumper."""
from artiq.experiment import *
from artiq.coredevice.core import Core
from artiq.coredevice.ttl import TTLOut, TTLInOut
from numpy import int64

@compile
class GenesysLoopback(EnvExperiment):
    core: KernelInvariant[Core]
    ttl: KernelInvariant[TTLOut]
    ttl_in: KernelInvariant[TTLInOut]

    def build(self):
        self.setattr_device("core")
        self.setattr_device("ttl")
        self.setattr_device("ttl_in")

    @rpc
    def report(self, start: int64, edge: int64):
        if edge < start or edge > start + 32:
            raise ValueError("Missing or incorrectly timed physical TTL edge")
        print("TTL_LOOPBACK_PASS", start, edge, edge-start, flush=True)

    @kernel
    def run(self):
        self.core.reset()
        # 20 ms lead allows uncached PS↔PL CSR programming during bring-up.
        start = self.core.get_rtio_counter_mu() + int64(2500000)
        at_mu(start - int64(125000))
        end = self.ttl_in.gate_rising_mu(int64(250000))
        at_mu(start)
        self.ttl.pulse_mu(int64(12500))  # 100 us
        edge = self.ttl_in.timestamp_mu(end)
        self.report(start, edge)
