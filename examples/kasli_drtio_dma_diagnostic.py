"""Physical DDR DMA -> JB1/JB2 captured by Kasli; LGPL-3.0-or-later.

Host DAP arms the native FPGA DMA via synchronous RPC. NOT native AUX DDMA.
Run only inside the reviewed external-session parent with both board leases.
"""
from artiq.experiment import *
from artiq.coredevice.core import Core
from artiq.coredevice.ttl import TTLInOut
from numpy import int64

@compile
class KasliSatelliteDMADiagnostic(EnvExperiment):
    core: KernelInvariant[Core]
    ttl_in: KernelInvariant[TTLInOut]

    def build(self):
        self.setattr_device('core')
        self.setattr_device('ttl_in')

    @rpc
    def arm(self,timestamp:int64):
        import os,sys
        from pathlib import Path
        sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'diagnostics/drtio'))
        from satellite_dma_probe import run_probe
        run_probe(os.environ['SATELLITE_DMA_CONFIG'],os.environ['SATELLITE_DMA_OUTPUT'],int(timestamp))

    @rpc
    def report(self,first_delta:int64):
        print('SATELLITE_DDR_DMA_PHYSICAL_PASS edges=8 width_mu=8000 period_mu=80000 first_delta_mu='+str(first_delta),flush=True)

    @kernel
    def run(self):
        self.core.reset()
        self.core.delay(0.01)
        start=self.core.get_rtio_counter_mu()+int64(30000000000)
        self.arm(start)
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
        self.report(first-start)
