"""Physical Kasli -> DRTIO -> Genesys JB1/JB2 loopback; LGPL-3.0-or-later.

Requires the qualified direct-link destination1 leaf, JB1 -> JB2 jumper.
No EEM outputs or other PMOD pins are used. Tests edge count plus timestamp
spacing; not absolute inter-board phase or deterministic link latency.
"""
from artiq.experiment import *
from artiq.coredevice.core import Core
from artiq.coredevice.ttl import TTLOut, TTLInOut
from numpy import int32, int64

@compile
class KasliDRTIODIO(EnvExperiment):
    core: KernelInvariant[Core]
    ttl_out: KernelInvariant[TTLOut]
    ttl_in: KernelInvariant[TTLInOut]

    def build(self):
        self.setattr_device('core')
        self.setattr_device('ttl_out')
        self.setattr_device('ttl_in')

    @rpc
    def report(self, edges:int32, spacing:int64):
        if edges!=8 or spacing!=100000:
            raise ValueError('Physical DRTIO TTL count/spacing mismatch')
        print('DRTIO_DIO_PASS',edges,spacing,flush=True)

    @kernel
    def run(self):
        self.core.reset()
        self.core.delay(0.01)
        self.ttl_out.off()
        self.core.delay(0.001)
        end=int64(0)
        with parallel:
            end=self.ttl_in.gate_rising(0.002)
            with sequential:
                self.core.delay(0.0001)
                for i in range(8):
                    self.ttl_out.pulse(0.00001)
                    self.core.delay(0.00009)
        first=self.ttl_in.timestamp_mu(end)
        previous=first
        edges=int32(1)
        spacing=int64(0)
        for i in range(7):
            current=self.ttl_in.timestamp_mu(end)
            assert current>previous
            spacing=current-previous
            assert spacing==int64(100000)
            previous=current
            edges+=1
        assert self.ttl_in.timestamp_mu(end)==int64(-1)
        assert first>int64(0)
        self.report(edges,spacing)
