"""Full32-slot limit, nested recording, DDMA rejection and pointer validation."""
from artiq.experiment import *
from artiq.coredevice.core import Core
from artiq.coredevice.dma import CoreDMA, dma_playback
from artiq.coredevice.ttl import TTLOut
from artiq.coredevice.exceptions import DMAError
from numpy import int32, int64

@compile
class GenesysDMAStoreLimits(EnvExperiment):
    core: KernelInvariant[Core]
    core_dma: KernelInvariant[CoreDMA]
    ttl: KernelInvariant[TTLOut]
    def build(self):
        self.setattr_device("core")
        self.setattr_device("core_dma")
        self.setattr_device("ttl")
    @rpc
    def report(self, mask: int32):
        print("COREDMA_LIMITS_RESULT",mask,flush=True)
        if mask==15:print("COREDMA_LIMITS_PASS",flush=True)
    @kernel
    def run(self):
        self.core.reset()
        mask=int32(0)
        self.core_dma.erase("genesys_core_dma")
        names=['dma_limit_00', 'dma_limit_01', 'dma_limit_02', 'dma_limit_03', 'dma_limit_04', 'dma_limit_05', 'dma_limit_06', 'dma_limit_07', 'dma_limit_08', 'dma_limit_09', 'dma_limit_10', 'dma_limit_11', 'dma_limit_12', 'dma_limit_13', 'dma_limit_14', 'dma_limit_15', 'dma_limit_16', 'dma_limit_17', 'dma_limit_18', 'dma_limit_19', 'dma_limit_20', 'dma_limit_21', 'dma_limit_22', 'dma_limit_23', 'dma_limit_24', 'dma_limit_25', 'dma_limit_26', 'dma_limit_27', 'dma_limit_28', 'dma_limit_29', 'dma_limit_30', 'dma_limit_31', 'dma_limit_32']
        for name in names:self.core_dma.erase(name)
        for i in range(32):
            self.core_dma.prepare_record(names[i])
            with self.core_dma.recorder:self.ttl.off()
        try:
            self.core_dma.prepare_record(names[32])
            with self.core_dma.recorder:self.ttl.off()
        except DMAError:mask=mask+1
        for name in names:self.core_dma.erase(name)
        self.core_dma.prepare_record("dma_nested")
        with self.core_dma.recorder:
            try:self.core_dma.recorder.__enter__()
            except DMAError:mask=mask+2
            self.ttl.off()
        self.core_dma.erase("dma_nested")
        try:
            self.core_dma.prepare_record("dma_ddma",True)
            with self.core_dma.recorder:self.ttl.off()
        except DMAError:mask=mask+4
        try:dma_playback(int64(0),int32(1),False)
        except DMAError:mask=mask+8
        self.report(mask)
