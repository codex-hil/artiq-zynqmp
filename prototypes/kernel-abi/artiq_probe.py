"""Offline compilation with actual ARTIQ Core/EnvExperiment/TTLOut classes."""
from artiq.experiment import *
from artiq.coredevice.core import Core
from artiq.coredevice.ttl import TTLOut
from artiq.language.embedding_map import EmbeddingMap
from numpy import int64


@extern
def abi_check64(value: int64):
    raise NotImplementedError


@extern
def abi_check_float(value: float) -> float:
    raise NotImplementedError


@compile
class ArtiqProbe(EnvExperiment):
    core: KernelInvariant[Core]
    ttl: KernelInvariant[TTLOut]

    def build(self):
        self.setattr_device("core")
        self.setattr_device("ttl")

    @kernel
    def run(self):
        self.core.reset()
        abi_check64(int64(0x1234567887654321))
        abi_check_float(abi_check_float(1.25))
        at_mu(int64(0x100000020))
        self.ttl.pulse_mu(int64(50))
        abi_check64(now_mu())


class OfflineDevices:
    def __init__(self):
        # host=None selects upstream CommKernelDummy; no network connection.
        self.core = Core(self, host=None, ref_period=8e-9, ref_multiplier=1, target="cortexa9")
        self.ttl = TTLOut(self, channel=0)

    def get(self, name):
        return getattr(self, name)


if __name__ == "__main__":
    devices = OfflineDevices()
    experiment = ArtiqProbe((devices, None, None, {}))
    devices.core.compile(experiment.run, [], {}, EmbeddingMap(),
                         output_filename="module.elf", debug_filename="debug.elf")
