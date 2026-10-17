"""One-shot arming and watchdog guard RTL; LGPL-3.0-or-later."""
import unittest,json,tempfile
from pathlib import Path
from migen import Module,Signal
from migen.sim import run_simulation
from litex.soc.interconnect.axi import AXIInterface
from dma_read_delay import DMAReadDelay
from dma_read_delay_control import ReadDelayControl,LabDelayedDMACSR,delay_cycles,verify_ps_clock


class ControlTests(unittest.TestCase):
    def test_imported_clock_must_be_unique_and_match(self):
        with tempfile.TemporaryDirectory() as name:
            p=Path(name)/'ps.xci'
            p.write_text(json.dumps({'ip_inst':{'parameters':{'component_parameters':{
                'PSU__CRL_APB__PL0_REF_CTRL__FREQMHZ':[{'value':'125'}]}}}}))
            self.assertEqual(verify_ps_clock([p],125000000)['configured_hz'],125000000)
            for ips,hz in [([p],100000000),([],125000000),([p,p],125000000)]:
                with self.assertRaises(ValueError):verify_ps_clock(ips,hz)
            p.write_text('{}')
            with self.assertRaises(ValueError):verify_ps_clock([p],125000000)

    def test_clock_conversion_and_invalid_parameters(self):
        self.assertEqual(delay_cycles(100000000),200000)
        self.assertEqual(delay_cycles(125000000),250000)
        for freq,us in [(0,2000),(100000000,1000),(100000000,20000)]:
            with self.assertRaises(ValueError):delay_cycles(freq,us)

    def test_arm_once_busy_reject_watchdog_and_no_automatic_repeat(self):
        d=Module();u,m=AXIInterface(),AXIInterface()
        d.submodules.g=g=DMAReadDelay(u,m,5)
        launch,idle,watchdog=Signal(),Signal(),Signal(32)
        d.submodules.c=c=ReadDelayControl(g,launch,idle,watchdog,5)
        def arm():
            yield c.arm.r.eq(1);yield c.arm.re.eq(1);yield
            yield c.arm.re.eq(0);yield
        def start():
            yield launch.eq(1);yield
            yield launch.eq(0);yield
            for _ in range(10):yield
        def run():
            yield watchdog.eq(11)
            yield from arm()
            self.assertEqual((yield c.arm_rejected.status),1)
            yield idle.eq(1);yield
            yield from arm()
            self.assertEqual((yield c.armed.status),1)
            yield from arm()
            self.assertEqual((yield c.arm_rejected.status),2)
            yield from start()
            self.assertEqual((yield c.triggers.status),1)
            self.assertEqual((yield c.armed.status),0)
            self.assertEqual((yield g.holding),0)
            yield from start()
            self.assertEqual((yield c.triggers.status),1)
            yield from arm();yield watchdog.eq(10);yield
            yield from start()
            self.assertEqual((yield c.rejected.status),1)
            self.assertEqual((yield c.triggers.status),1)
            self.assertEqual((yield c.armed.status),0)
            # A memory response already visible at launch also consumes
            # the one-shot, but cannot hide that response or count success.
            yield watchdog.eq(11);yield from arm()
            yield m.r.valid.eq(1);yield
            yield from start()
            self.assertEqual((yield c.rejected.status),2)
            self.assertEqual((yield c.triggers.status),1)
            self.assertEqual((yield c.armed.status),0)
            self.assertEqual((yield u.r.valid),1)
        run_simulation(d,run())

    def test_variant_preserves_base_csr_addresses(self):
        from dma_csr import DMACSR
        bus=lambda:AXIInterface(data_width=64,address_width=49,id_width=6)
        base=DMACSR(bus()).memory_map(0xa0002000)
        lab=LabDelayedDMACSR(bus(),sys_clk_hz=100000000).memory_map(0xa0002000)
        for name,entry in base['registers'].items():self.assertEqual(lab['registers'][name],entry)
        self.assertEqual(lab['laboratory_read_delay']['cycles'],200000)
        self.assertIn('dma_lab_delay_arm',lab['registers'])
