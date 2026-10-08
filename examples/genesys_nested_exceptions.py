"""Nested exception, reraise and finally execution on the physical worker."""
from artiq.experiment import *
from artiq.coredevice.core import Core
from numpy import int32

@compile
class GenesysNestedExceptions(EnvExperiment):
    core: KernelInvariant[Core]
    def build(self):
        self.setattr_device("core")
    @rpc
    def report(self, value: int32):
        print("NESTED_EXCEPTION_RESULT", value, flush=True)
        if value == 7:
            print("NESTED_EXCEPTION_PASS", flush=True)
    @kernel
    def run(self):
        value = int32(0)
        try:
            try:
                raise ValueError("first exception")
            except ValueError:
                value = value + 1
                raise
            finally:
                value = value + 2
        except ValueError:
            value = value + 4
        self.report(value)
