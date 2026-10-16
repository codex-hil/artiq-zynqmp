"""Host-only physical abort cancellation/handoff; LGPL-3.0-or-later.

Requires the reviewed all-board parent and explicit abort configuration.
No core.reset or DMA restart after abort. JB1->JB2 only.
"""
from artiq.experiment import *
from artiq.coredevice.core import Core
from artiq.coredevice.ttl import TTLOut, TTLInOut
from numpy import int64

@compile
class KasliSatelliteDMAAbort(EnvExperiment):
    core: KernelInvariant[Core]
    ttl_in: KernelInvariant[TTLInOut]
    ttl_out: KernelInvariant[TTLOut]

    def build(self):
        self.setattr_device('core')
        self.setattr_device('ttl_in')
        self.setattr_device('ttl_out')

    @rpc
    def abort(self,timestamp:int64):
        import os,sys
        from pathlib import Path
        sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'diagnostics/drtio'))
        from satellite_dma_probe import run_probe
        run_probe(os.environ['SATELLITE_DMA_CONFIG'],os.environ['SATELLITE_DMA_OUTPUT'],int(timestamp))

    @rpc
    def report(self):
        print('SATELLITE_DMA_ABORT_PHYSICAL_PASS canceled_edges=0 packet_edges=2 width_mu=8000',flush=True)

    @kernel
    def run(self):
        self.core.reset()
        self.core.delay(0.01)
        self.ttl_out.off()
        start=self.core.get_rtio_counter_mu()+int64(30000000000)
        self.abort(start)
        assert self.core.get_rtio_counter_mu()<start-int64(2000000)
        # Rearm input after abort reset, covering every canceled timestamp.
        at_mu(start-int64(1000000))
        end=self.ttl_in.gate_both_mu(int64(21000000))
        assert self.ttl_in.timestamp_mu(end)==int64(-1)
        self.core.break_realtime()
        with parallel:
            end=self.ttl_in.gate_both_mu(int64(1000000))
            with sequential:
                delay_mu(int64(100000))
                self.ttl_out.on()
                delay_mu(int64(8000))
                self.ttl_out.off()
        rise=self.ttl_in.timestamp_mu(end)
        fall=self.ttl_in.timestamp_mu(end)
        assert rise>int64(0)
        assert fall-rise==int64(8000)
        assert self.ttl_in.timestamp_mu(end)==int64(-1)
        self.report()
