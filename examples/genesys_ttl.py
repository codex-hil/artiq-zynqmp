"""Minimal compileable Genesys local-RTIO output experiment.

Compilation is verified; physical execution awaits network kernel runtime.
"""
from artiq.experiment import *
from numpy import int64
from artiq.coredevice.core import Core
from artiq.coredevice.ttl import TTLOut


@compile
class GenesysTTL(EnvExperiment):
    core: KernelInvariant[Core]
    ttl: KernelInvariant[TTLOut]

    def build(self):
        self.setattr_device("core")
        self.setattr_device("ttl")

    @kernel
    def run(self):
        self.core.reset()
        self.ttl.pulse_mu(int64(125))  # 1 us at the local-RTIO 8 ns reference period.
