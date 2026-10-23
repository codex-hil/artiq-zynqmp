"""Bounded diagnostic CoreDMA load; physical TTL outputs, not a loopback proof."""
from artiq.experiment import *
from artiq.coredevice.core import Core
from artiq.coredevice.dma import CoreDMA
from artiq.coredevice.ttl import TTLOut
from numpy import int32,int64

@compile
class GenesysDMAObserverLoad(EnvExperiment):
    core: KernelInvariant[Core]
    core_dma: KernelInvariant[CoreDMA]
    ttl: KernelInvariant[TTLOut]
    def build(self):
        self.setattr_device('core')
        self.setattr_device('core_dma')
        self.setattr_device('ttl')
    @rpc
    def report(self,phase:int32):
        print('DMA_OBSERVER_LOAD',phase,flush=True)
    @kernel
    def run(self):
        self.core.reset()
        self.core_dma.prepare_record('observer_bounded')
        with self.core_dma.recorder:
            for i in range(128):
                self.ttl.pulse_mu(int64(12500))
                delay_mu(int64(12500))
        handle=self.core_dma.get_handle('observer_bounded')
        if handle[1]!=int64(3200000):
            raise ValueError('Unexpected observer DMA trace duration')
        self.report(int32(1))
        for repeat in range(512):
            start=self.core.get_rtio_counter_mu()+int64(6250000)
            at_mu(start)
            self.core_dma.playback_handle(handle)
        self.core.wait_until_mu(now_mu())
        self.report(int32(2))
