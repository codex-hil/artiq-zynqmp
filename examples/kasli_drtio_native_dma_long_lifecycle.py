"""Standard distributed CoreDMA physical TTL loopback; LGPL-3.0-or-later.

Run only in the all-board guarded session. No host DAP upload/arming.
"""
from artiq.experiment import *
from artiq.coredevice.core import Core
from artiq.coredevice.dma import CoreDMA
from artiq.coredevice.ttl import TTLOut, TTLInOut
from numpy import int64

@compile
class KasliNativeDDMALongLifecycle(EnvExperiment):
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
    def report(self,phase:int64,replay:int64,width:int64,period:int64,first_delta:int64):
        print('NATIVE_DDMA_LONG_LIFECYCLE_PASS phase='+str(phase)+' replay='+str(replay)+
              ' edges=58 width_mu='+str(width)+' period_mu='+str(period)+
              ' first_delta_mu='+str(first_delta),flush=True)

    @kernel
    def run(self):
        self.core.reset()
        self.core.delay(0.01)
        for phase in range(3):
            width=int64(4000)+int64(phase)*int64(2000)
            period=int64(16000)+int64(phase)*int64(4000)
            # phase1 replaces the existing name; phase2 uploads after erase.
            self.core_dma.prepare_record('genesys_native_ddma',enable_ddma=True)
            with self.core_dma.recorder:
                self.ttl_in._set_sensitivity(3)
                delay_mu(int64(1000000))
                for i in range(29):
                    self.ttl_out.on()
                    delay_mu(width)
                    self.ttl_out.off()
                    delay_mu(period-width)
                delay_mu(int64(1000000)-int64(29)*period)
                self.ttl_in._set_sensitivity(0)
            handle=self.core_dma.get_handle('genesys_native_ddma')
            for replay in range(3):
                self.core.break_realtime()
                self.core.delay(0.05)
                start=now_mu()
                if replay==0:
                    self.core_dma.playback('genesys_native_ddma')
                else:
                    self.core_dma.playback_handle(handle)
                end=start+int64(3000000)
                first=int64(0)
                previous=int64(0)
                for i in range(29):
                    rise=self.ttl_in.timestamp_mu(end)
                    fall=self.ttl_in.timestamp_mu(end)
                    assert rise>int64(0)
                    assert fall-rise==width
                    if i==0:
                        first=rise
                    else:
                        assert rise-previous==period
                    previous=rise
                assert first-start>=int64(1000000)
                assert first-start<int64(1100000)
                assert self.ttl_in.timestamp_mu(end)==int64(-1)
                self.report(int64(phase),int64(replay),width,period,first-start)
            if phase!=0:
                self.core_dma.erase('genesys_native_ddma')
