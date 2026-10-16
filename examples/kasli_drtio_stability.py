"""4096 measured external DRTIO edges across two wrapper runs; LGPL-3.0-or-later.

Each kernel measures1024 pulses, both edge timestamps and empty FIFO after
16-edge batches. Four widths/periods, periodic native RTIO resets. Not a link
loss/retraining or absolute phase measurement. Requires JB1 -> JB2 jumper.
"""
from artiq.experiment import *
from artiq.coredevice.core import Core
from artiq.coredevice.ttl import TTLOut, TTLInOut
from numpy import int32, int64

@compile
class KasliDRTIOStability(EnvExperiment):
    core: KernelInvariant[Core]
    ttl_out: KernelInvariant[TTLOut]
    ttl_in: KernelInvariant[TTLInOut]

    def build(self):
        self.setattr_device('core')
        self.setattr_device('ttl_out')
        self.setattr_device('ttl_in')

    @rpc
    def report(self,edges:int32,batches:int32):
        if edges!=2048 or batches!=128:
            raise ValueError('DRTIO stability coverage mismatch')
        print('DRTIO_STABILITY_PASS',edges,batches,flush=True)

    @kernel
    def run(self):
        edges=int32(0)
        for batch in range(128):
            if batch%32==0:
                self.core.reset()
            self.core.delay(0.01)
            self.ttl_out.off()
            self.core.delay(0.001)
            width=int64(800)
            period=int64(16000)
            if batch%4==1:
                width=int64(8000)
                period=int64(40000)
            if batch%4==2:
                width=int64(10000)
                period=int64(100000)
            if batch%4==3:
                width=int64(30000)
                period=int64(250000)
            end=int64(0)
            with parallel:
                end=self.ttl_in.gate_both_mu(period*int64(8)+int64(200000))
                with sequential:
                    self.core.delay(0.0001)
                    for pulse in range(8):
                        self.ttl_out.pulse_mu(width)
                        self.core.delay(float(period-width)*1e-9)
            previous=int64(0)
            for pulse in range(8):
                rise=self.ttl_in.timestamp_mu(end)
                fall=self.ttl_in.timestamp_mu(end)
                assert rise>int64(0)
                assert fall-rise==width
                if pulse>0:
                    assert rise-previous==period
                previous=rise
                edges+=2
            assert self.ttl_in.timestamp_mu(end)==int64(-1)
        self.report(edges,int32(128))
