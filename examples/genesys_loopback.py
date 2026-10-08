"""Physical JB1→JB2 loopback: timestamps of both edges and 100 us width."""
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
    def report(self, start: int64, edge: int64, fall: int64, extra: int64):
        print("TTL_LOOPBACK_RESULT", start, edge, fall, extra, flush=True)
        if edge < start or edge > start + 32 or fall - edge != 12500 or extra != -1:
            # Report failure without a host RPCException: this bring-up runtime
            # cannot recover from those yet. The hardware runner rejects FAIL.
            print("TTL_LOOPBACK_FAIL", flush=True)
        else:
            print("TTL_LOOPBACK_PASS", start, edge, fall, edge-start, fall-edge, flush=True)

    @kernel
    def run(self):
        self.core.reset()
        # 20 ms lead allows uncached PS↔PL CSR programming during bring-up.
        start = self.core.get_rtio_counter_mu() + int64(2500000)
        at_mu(start - int64(125000))
        end = self.ttl_in.gate_both_mu(int64(250000))
        at_mu(start)
        self.ttl.pulse_mu(int64(12500))  # 100 us
        edge = self.ttl_in.timestamp_mu(end)
        fall = self.ttl_in.timestamp_mu(end)
        extra = self.ttl_in.timestamp_mu(end)
        self.report(start, edge, fall, extra)
