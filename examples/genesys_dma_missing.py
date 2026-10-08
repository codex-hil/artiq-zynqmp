"""Negative control: missing trace must propagate a real host DMAError."""
from artiq.experiment import *
from artiq.coredevice.core import Core
from artiq.coredevice.dma import CoreDMA

@compile
class GenesysDMAMissing(EnvExperiment):
    core: KernelInvariant[Core]
    core_dma: KernelInvariant[CoreDMA]
    def build(self):
        self.setattr_device("core")
        self.setattr_device("core_dma")
    @kernel
    def run(self):
        self.core_dma.erase("missing_negative_control")
        self.core_dma.playback("missing_negative_control")
