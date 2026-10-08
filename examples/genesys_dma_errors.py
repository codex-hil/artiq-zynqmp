"""CoreDMA lifecycle errors, overwrite, capacity, and native DMA underflow."""
from artiq.experiment import *
from artiq.coredevice.core import Core
from artiq.coredevice.dma import CoreDMA, dma_playback
from artiq.coredevice.ttl import TTLOut
from artiq.coredevice.exceptions import DMAError, RTIOUnderflow
from numpy import int32, int64

@compile
class GenesysDMAErrors(EnvExperiment):
    core: KernelInvariant[Core]
    core_dma: KernelInvariant[CoreDMA]
    ttl: KernelInvariant[TTLOut]
    def build(self):
        self.setattr_device("core")
        self.setattr_device("core_dma")
        self.setattr_device("ttl")
    @rpc
    def report(self, mask: int32):
        print("COREDMA_ERRORS_RESULT",mask,flush=True)
        if mask==255:print("COREDMA_ERRORS_PASS",flush=True)
    @kernel
    def run(self):
        self.core.reset()
        mask=int32(0)
        try:
            self.core_dma.get_handle("missing_dma_trace")
        except DMAError:mask=mask+1
        self.core_dma.prepare_record("dma_errors")
        with self.core_dma.recorder:
            self.ttl.pulse_mu(int64(12500))
        old=self.core_dma.get_handle("dma_errors")
        self.core_dma.prepare_record("dma_errors")
        with self.core_dma.recorder:
            delay_mu(int64(1000))
            self.ttl.pulse_mu(int64(25000))
        handle=self.core_dma.get_handle("dma_errors")
        if handle[1]==int64(26000):mask=mask+2
        try:
            self.core_dma.playback_handle(old)
        except DMAError:mask=mask+4
        at_mu(int64(0))
        try:
            self.core_dma.playback_handle(handle)
        except RTIOUnderflow:mask=mask+8
        # Error was acknowledged; the same hardware engine must work again.
        at_mu(self.core.get_rtio_counter_mu()+int64(6250000))
        self.core_dma.playback_handle(handle)
        self.core.wait_until_mu(now_mu())
        self.core_dma.erase("dma_errors")
        try:
            dma_playback(self.core.get_rtio_counter_mu()+int64(6250000),handle[2],False)
        except DMAError:mask=mask+16
        try:
            self.core_dma.prepare_record("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
            with self.core_dma.recorder:self.ttl.off()
        except DMAError:mask=mask+32
        try:
            self.core_dma.prepare_record("dma_too_big")
            with self.core_dma.recorder:
                for i in range(4000):self.ttl.off()
        except DMAError:mask=mask+64
        # Empty trace and empty name: duration preserved, no RTIO events.
        self.core_dma.prepare_record("")
        with self.core_dma.recorder:delay_mu(int64(100))
        empty=self.core_dma.get_handle("")
        at_mu(self.core.get_rtio_counter_mu()+int64(6250000))
        self.core_dma.playback_handle(empty)
        if empty[1]==int64(100):mask=mask+128
        self.core_dma.erase("")
        self.report(mask)
