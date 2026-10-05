"""Actual NAC3 kernel; min_artiq is supplied by the pinned compiler checkout.

The runtime records calls instead of driving hardware. Distinct constants check
64-bit argument order/alignment and hard-float calls across the loader boundary.
"""
from min_artiq import *
from min_artiq import rtio_output
from numpy import int32, int64


@extern
def abi_check64(value: int64):
    raise NotImplementedError


@extern
def abi_check_float(value: float) -> float:
    raise NotImplementedError


@compile
class Probe:
    core: KernelInvariant[Core]

    def __init__(self):
        self.core = Core()

    @kernel
    def run(self):
        self.core.reset()
        abi_check64(int64(0x1234567887654321))
        abi_check_float(abi_check_float(1.25))
        at_mu(int64(0x100000020))
        rtio_output(int32(0), int32(1))
        delay_mu(int64(50))
        rtio_output(int32(0), int32(0))
        abi_check64(now_mu())


if __name__ == "__main__":
    Probe().run()
