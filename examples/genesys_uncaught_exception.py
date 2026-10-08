"""Uncaught native kernel exception with host reconstruction and traceback."""
from artiq.experiment import *
from artiq.coredevice.core import Core

@compile
class GenesysUncaughtException(EnvExperiment):
    core: KernelInvariant[Core]
    def build(self):
        self.setattr_device("core")
    @kernel
    def run(self):
        raise ValueError("intentional uncaught kernel failure")
