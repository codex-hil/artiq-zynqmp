"""Fill the real 64-entry input FIFO, catch overflow and reset local RTIO."""
from artiq.experiment import *
from artiq.coredevice.core import Core
from artiq.coredevice.rtio import rtio_output, rtio_input_timestamp
from artiq.coredevice.exceptions import RTIOOverflow
from numpy import int32, int64

@compile
class GenesysRTIOOverflow(EnvExperiment):
    core: KernelInvariant[Core]
    def build(self):
        self.setattr_device("core")
    @rpc
    def report(self, caught: int32):
        print("RTIO_OVERFLOW_RESULT", caught, flush=True)
        if caught == 1:
            print("RTIO_OVERFLOW_PASS", flush=True)
    @kernel
    def run(self):
        self.core.reset()
        at_mu(self.core.get_rtio_counter_mu() + int64(2500000))
        for i in range(80):
            rtio_output(int32(0x103), int32(0))
            delay_mu(int64(12500))
        self.core.wait_until_mu(now_mu() + int64(125000))
        caught = int32(0)
        try:
            timestamp = rtio_input_timestamp(int64(0), int32(1))
        except RTIOOverflow:
            caught = int32(1)
        self.core.reset()
        self.report(caught)
