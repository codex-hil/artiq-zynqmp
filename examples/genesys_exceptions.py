"""Catch kernel/RPC/RTIO exceptions and prove execution continues."""
from artiq.experiment import *
from artiq.coredevice.core import Core
from artiq.coredevice.rtio import rtio_output
from artiq.coredevice.exceptions import RTIOUnderflow
from numpy import int32, int64

@compile
class GenesysExceptions(EnvExperiment):
    core: KernelInvariant[Core]
    def build(self):
        self.setattr_device("core")
    @rpc
    def broken_rpc(self) -> int32:
        raise ValueError("intentional host RPC failure")
    @rpc
    def report(self, caught: int32):
        print("EXCEPTION_CATCH_RESULT", caught, flush=True)
        if caught == 7:
            print("EXCEPTION_CATCH_PASS", flush=True)
    @kernel
    def run(self):
        caught = int32(0)
        try:
            raise ValueError("intentional kernel failure")
        except ValueError:
            caught = caught + 1
        self.core.reset()
        try:
            at_mu(int64(0))
            rtio_output(int32(0x103), int32(0))
        except RTIOUnderflow:
            caught = caught + 2
        try:
            value = self.broken_rpc()
        except ValueError:
            caught = caught + 4
        self.report(caught)
