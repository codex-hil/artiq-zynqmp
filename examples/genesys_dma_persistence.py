"""Real CoreDMA recorder/handle playback, four physical JB1→JB2 pulses."""
from artiq.experiment import *
from artiq.coredevice.core import Core
from artiq.coredevice.dma import CoreDMA
from artiq.coredevice.exceptions import DMAError
from artiq.coredevice.ttl import TTLOut, TTLInOut
from numpy import int32, int64

@compile
class GenesysDMAPersistence(EnvExperiment):
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
        if valid==8 and first-start==1250015 and duration==1350000 and extra==-1:
            print("COREDMA_LOOPBACK_PASS",start,first,duration,extra,flush=True)
    @kernel
    def record(self):
        self.core_dma.prepare_record("genesys_core_dma")
        with self.core_dma.recorder:
            delay_mu(int64(1250000))
            for i in range(4):
                self.ttl.pulse_mu(int64(12500))
                delay_mu(int64(12500))
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
        for i in range(8):
            edge=self.ttl_in.timestamp_mu(end)
            if i==0:first=edge
            expected=start+int64(1250000)+int64(i//2)*int64(25000)+int64(i%2)*int64(12500)+int64(15)
            if edge==expected:valid=valid+1
        extra=self.ttl_in.timestamp_mu(end)
        self.report(valid,start,first,handle[1],extra)
    @kernel
    def intentional_exception(self):
        self.core_dma.prepare_record("genesys_dma_abandoned")
        # Simulate an uncaught exception with an active, incomplete recorder.
        self.core_dma.recorder.__enter__()
        self.ttl.on()
        raise ValueError("intentional exception while recording DMA")
    @kernel
    def erase_and_check(self):
        from_error=int32(0)
        self.core_dma.erase("genesys_core_dma")
        try:
            self.core_dma.get_handle("genesys_core_dma")
        except DMAError:
            from_error=from_error+1
        try:
            self.core_dma.get_handle("genesys_dma_abandoned")
        except DMAError:
            from_error=from_error+2
        if from_error!=3:raise ValueError("DMA erase/aborted recorder validation failed")
    def run(self):
        self.record()
        self.verify(False)
        connection=self.core.comm.socket
        try:
            self.intentional_exception()
        except ValueError as error:
            if "intentional exception while recording DMA" not in str(error):raise
        else:
            raise RuntimeError("DMA recorder exception was not propagated")
        self.verify(True)
        if self.core.comm.socket is not connection:
            raise RuntimeError("Connection changed across DMA exception recovery")
        self.erase_and_check()
        print("COREDMA_PERSISTENCE_PASS",flush=True)
