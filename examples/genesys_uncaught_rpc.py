"""Uncaught host RPC error: expect ValueError and subsequent kernel recovery."""
from artiq.experiment import *
from artiq.coredevice.core import Core
from numpy import int32

@compile
class GenesysUncaughtRPC(EnvExperiment):
    core: KernelInvariant[Core]
    def build(self):
        self.setattr_device("core")
    @rpc
    def broken(self) -> int32:
        raise ValueError("intentional uncaught RPC failure")
    @kernel
    def run(self):
        result = self.broken()
