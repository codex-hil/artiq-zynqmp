"""Real CoreDMA recorder/handle playback, 24 physical64ns pulses,64ns gaps."""
from artiq.experiment import *
from artiq.coredevice.core import Core
from artiq.coredevice.dma import CoreDMA
from artiq.coredevice.ttl import TTLOut, TTLInOut
from numpy import int32, int64

@compile
class GenesysDMATight(EnvExperiment):
    core: KernelInvariant[Core]
    core_dma: KernelInvariant[CoreDMA]
    ttl: KernelInvariant[TTLOut]
    ttl_in: KernelInvariant[TTLInOut]
    def build(self):
        self.setattr_device("core")
        self.setattr_device("core_dma")
        self.setattr_device("ttl")
        self.setattr_device("ttl_in")
    @rpc
    def report(self, valid: int32, start: int64, first: int64, duration: int64, extra: int64):
        print("COREDMA_RESULT",valid,start,first,duration,extra,flush=True)
        if valid==48 and first-start==1250015 and duration==1250384 and extra==-1:
            print("COREDMA_TIGHT_PASS",start,first,duration,extra,flush=True)
    @kernel
    def record(self):
        self.core_dma.prepare_record("genesys_core_dma")
        with self.core_dma.recorder:
            delay_mu(int64(1250000))
            for i in range(24):
                self.ttl.pulse_mu(int64(8))
                delay_mu(int64(8))
    @kernel
    def verify(self, by_name: bool):
        self.core.reset()
        handles=[self.core_dma.get_handle("genesys_core_dma")]
        handle=handles[0]
        start=self.core.get_rtio_counter_mu()+int64(6250000)
        at_mu(start)
        end=self.ttl_in.gate_both_mu(int64(2000000))
        at_mu(start)
        if by_name:self.core_dma.playback("genesys_core_dma")
        else:self.core_dma.playback_handle(handle)
        if now_mu()!=start+handle[1]:
            raise ValueError("DMA playback did not advance timeline")
        valid=int32(0)
        first=int64(0)
        for i in range(48):
            edge=self.ttl_in.timestamp_mu(end)
            if i==0:first=edge
            expected=start+int64(1250000)+int64(i//2)*int64(16)+int64(i%2)*int64(8)+int64(15)
            if edge==expected:valid=valid+1
        extra=self.ttl_in.timestamp_mu(end)
        self.report(valid,start,first,handle[1],extra)
    @kernel
    def run(self):
        self.core.reset()
        before=now_mu()
        self.record()
        if now_mu()!=before:raise ValueError("DMA recording changed caller timeline")
        self.verify(False)
        self.verify(True)
