"""Negative control: past input-sample event; requires worker restart afterward."""
from artiq.experiment import *
from artiq.coredevice.core import Core
from artiq.coredevice.rtio import rtio_output
from numpy import int32, int64

@compile
class GenesysRTIOUnderflow(EnvExperiment):
    core: KernelInvariant[Core]
    def build(self):
        self.setattr_device("core")
    @kernel
    def run(self):
        self.core.reset()
        at_mu(int64(0))
        rtio_output(int32(0x103), int32(0))
