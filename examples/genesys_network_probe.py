"""Real host/device kernel+RPC test; reads counter, never outputs TTL."""
from artiq.experiment import *
from artiq.coredevice.core import Core
from numpy import int64
import os
import time


@compile
class GenesysNetworkProbe(EnvExperiment):
    core: KernelInvariant[Core]

    def build(self):
        self.setattr_device("core")

    @rpc
    def report(self, token: int64, counter: int64, value: float) -> float:
        if token != 0x1234567887654321 or counter <= 0 or value != 1.25:
            raise ValueError("Incorrect physical kernel/RPC values")
        print("NETWORK_KERNEL_RPC", hex(token), counter, value, flush=True)
        time.sleep(float(os.environ.get("GENESYS_TEST_RPC_DELAY", "0")))
        return value + 2.5

    @rpc
    def confirm(self, value: float):
        if value != 3.75:
            raise ValueError("Incorrect synchronous RPC return value")
        print("NETWORK_KERNEL_RETURN_PASS", value)

    @kernel
    def run(self):
        self.core.reset()
        value = self.report(int64(0x1234567887654321), self.core.get_rtio_counter_mu(), 1.25)
        self.confirm(value)
