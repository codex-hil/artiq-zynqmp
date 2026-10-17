"""Standard distributed CoreDMA physical TTL loopback; LGPL-3.0-or-later.

Catch upload DMAError and record/play a valid trace in the same kernel.
Exactly one initial core.reset; no reset/restart between failure and recovery.
Run only in the all-board guarded session. No host DAP upload/arming.
"""
from artiq.experiment import *
from artiq.coredevice.core import Core
from artiq.coredevice.dma import CoreDMA
from artiq.coredevice.exceptions import DMAError
from artiq.coredevice.ttl import TTLOut, TTLInOut
from numpy import int64

@compile
class KasliNativeDDMACatch(EnvExperiment):
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
    def report(self,first_delta:int64):
        print('NATIVE_DDMA_PHYSICAL_PASS edges=8 width_mu=8000 period_mu=80000 first_delta_mu='+str(first_delta),flush=True)

    @rpc
    def caught(self):
        print("NATIVE_DDMA_CAUGHT_PASS",flush=True)

    @kernel
    def run(self):
        self.core.reset()
        self.core.delay(0.01)
        caught=False
        try:
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
        except DMAError:
            caught=True
        assert caught
        self.caught()
        # Recording context exit may leave relative now on exception. Use the
        # standard scheduling resynchronization, not a core or kernel reset.
        self.core.break_realtime()
        self.core_dma.prepare_record('genesys_native_ddma',enable_ddma=True)
        with self.core_dma.recorder:
            self.ttl_in._set_sensitivity(3)
            delay_mu(int64(1000000))
            for i in range(4):
                self.ttl_out.on()
                delay_mu(int64(8000))
                self.ttl_out.off()
                delay_mu(int64(72000))
            delay_mu(int64(680000))
            self.ttl_in._set_sensitivity(0)
        # Upload has completed before playback. Leave ample lead for live TSC
        # sampling, cache flush, actual AXI admission and native AUX response.
        self.core.break_realtime()
        self.core.delay(0.05)
        start=now_mu()
        self.core_dma.playback('genesys_native_ddma')
        end=start+int64(3000000)
        first=int64(0)
        previous=int64(0)
        for i in range(4):
            rise=self.ttl_in.timestamp_mu(end)
            fall=self.ttl_in.timestamp_mu(end)
            assert rise>int64(0)
            assert fall-rise==int64(8000)
            if i==0:
                first=rise
            else:
                assert rise-previous==int64(80000)
            previous=rise
        assert first-start>=int64(1000000)
        assert first-start<int64(1100000)
        assert self.ttl_in.timestamp_mu(end)==int64(-1)
        self.core_dma.erase('genesys_native_ddma')
        self.report(first-start)
