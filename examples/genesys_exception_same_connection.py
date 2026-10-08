"""Host catches a device exception and reuses the exact same TCP connection."""
from artiq.experiment import *
from artiq.coredevice.core import Core
from artiq.coredevice.rtio import rtio_output
from artiq.coredevice.exceptions import RTIOUnderflow
from numpy import int32, int64

@compile
class GenesysExceptionSameConnection(EnvExperiment):
    core: KernelInvariant[Core]
    def build(self):
        self.setattr_device("core")
    @kernel
    def failing(self):
        self.core.reset()
        at_mu(int64(0))
        rtio_output(int32(0x103), int32(0))
    @rpc
    def report(self, counter: int64):
        if counter > 0:
            print("SAME_CONNECTION_KERNEL_PASS", counter, flush=True)
    @kernel
    def following(self):
        self.core.reset()
        self.report(self.core.get_rtio_counter_mu())
    def run(self):
        try:
            self.failing()
        except RTIOUnderflow as error:
            info = error.artiq_core_exception
            if not info.traceback or not info.name.endswith("RTIOUnderflow"):
                raise RuntimeError("Device exception lacks decoded traceback/type")
            print("DEVICE_TRACEBACK_PASS", info.traceback, flush=True)
        else:
            raise RuntimeError("Device failed to raise native RTIOUnderflow")
        connection = self.core.comm.socket
        self.following()
        if self.core.comm.socket is not connection:
            raise RuntimeError("Kernel connection was recreated")
        print("SAME_CONNECTION_RECOVERY_PASS", flush=True)
