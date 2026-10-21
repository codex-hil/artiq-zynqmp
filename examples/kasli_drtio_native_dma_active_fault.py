"""Opt-in lab active-underflow candidate, not hardware qualified. LGPL-3.0-or-later.

Only for a dedicated all-board guarded wrapper and delay image/firmware.
Normal native wrappers refuse that firmware. No automatic hardware access here.
"""
from artiq.experiment import *
from artiq.coredevice.core import Core
from artiq.coredevice.dma import CoreDMA
from artiq.coredevice.ttl import TTLOut
from artiq.coredevice.exceptions import RTIOUnderflow
from numpy import int64

@compile
class KasliNativeDDMAActiveFault(EnvExperiment):
    core: KernelInvariant[Core]
    core_dma: KernelInvariant[CoreDMA]
    ttl_out: KernelInvariant[TTLOut]

    def build(self):
        self.setattr_device('core')
        self.setattr_device('core_dma')
        self.setattr_device('ttl_out')

    @rpc
    def arm(self):
        import os,sys
        from pathlib import Path
        sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'diagnostics/drtio'))
        from dma_arm_handshake import arm
        directory=os.environ.get('ARTIQ_DDMA_LAB_HANDSHAKE')
        if not directory:raise RuntimeError('Dedicated leased laboratory wrapper required')
        arm(directory)

    @rpc
    def report(self,start:int64):
        print('NATIVE_DDMA_ACTIVE_UNDERFLOW_CAUGHT_PASS timestamp='+str(start),flush=True)

    @kernel
    def run(self):
        self.core.reset()
        self.core_dma.prepare_record('genesys_lab_fault',enable_ddma=True)
        with self.core_dma.recorder:
            self.ttl_out.on()
            delay_mu(int64(8000))
            self.ttl_out.off()
        # Upload is complete before the guarded parent is asked to arm.
        self.arm()
        # Measured admission transit consumed1.38ms on KASLI04. Keep the
        # backend1ms minimum and lab2ms hold; actual fault evidence still required.
        start=(self.core.get_rtio_counter_mu()+int64(3000000)) & int64(-8)
        at_mu(start)
        caught=False
        try:
            self.core_dma.playback('genesys_lab_fault')
        except RTIOUnderflow:
            caught=True
        assert caught
        self.report(start)
        # No retry, erase, clear or reset here. Parent must restore both boards.
