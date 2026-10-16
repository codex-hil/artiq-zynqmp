"""Standard distributed CoreDMA physical TTL loopback; LGPL-3.0-or-later.

Expected upload failure:62 records/1054 bytes >1024 policy.
Run only in the all-board guarded session. Never plays the oversized trace.
"""
from artiq.experiment import *
from artiq.coredevice.core import Core
from artiq.coredevice.dma import CoreDMA
from artiq.coredevice.ttl import TTLOut, TTLInOut
from numpy import int64

@compile
class KasliNativeDDMAOversize(EnvExperiment):
    core: KernelInvariant[Core]
    core_dma: KernelInvariant[CoreDMA]
    ttl_out: KernelInvariant[TTLOut]
    ttl_in: KernelInvariant[TTLInOut]

    def build(self):
        self.setattr_device('core')
        self.setattr_device('core_dma')
        self.setattr_device('ttl_out')
        self.setattr_device('ttl_in')

    @rpc
    def unexpected(self):
        print('NATIVE_DDMA_OVERSIZE_UNEXPECTED_ACCEPT',flush=True)

    @kernel
    def run(self):
        self.core.reset()
        self.core.delay(0.01)
        self.core_dma.prepare_record('genesys_native_ddma',enable_ddma=True)
        with self.core_dma.recorder:
            self.ttl_in._set_sensitivity(3)
            delay_mu(int64(1000000))
            for i in range(30):
                self.ttl_out.on()
                delay_mu(int64(8000))
                self.ttl_out.off()
                delay_mu(int64(8000))
            delay_mu(int64(520000))
            self.ttl_in._set_sensitivity(0)
        # Reaching here means the satellite incorrectly accepted1054 bytes.
        # Never call playback for the oversized trace.
        self.unexpected()
