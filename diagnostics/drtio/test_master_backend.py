"""Bounded native master/Kasli-style satellite RTL tests; LGPL-3.0-or-later.

Encoded raw20/ideal clocks only; no GT, AXI, AUX firmware or hardware credit.
"""
import unittest
from unittest.mock import patch
from migen.sim import run_simulation
from artiq.gateware import rtio
from artiq.gateware.test.drtio import test_full_stack as upstream
from master_backend import GenesysMasterBackend
from test_packets_raw20 import EncodedPair


class MasterBackendTests(unittest.TestCase):
    def make_tb(self):
        constructor = rtio.TSC
        with patch.object(upstream, 'DRTIOMaster', GenesysMasterBackend), \
             patch.object(upstream, 'DummyTransceiverPair', EncodedPair), \
             patch.object(upstream.rtio, 'TSC', lambda: constructor(glbl_fine_ts_width=3)):
            tb = upstream.OutputsTestbench()
        tb.dut.submodules.encoded_pair = tb.dut.transceivers
        return tb

    def exercise(self, underflow=False):
        tb = self.make_tb();dut=tb.dut;changes=[];done=[False];loads=[]
        def test():
            yield from tb.init()
            self.assertEqual(dut.tsc_master.glbl_fine_ts_width,3)
            self.assertEqual(dut.tsc_satellite.glbl_fine_ts_width,3)
            if underflow:
                with self.assertRaises(upstream.RTIOUnderflow):
                    yield from tb.write(0,1)
                for _ in range(40):yield
            else:
                yield from dut.master.rt_controller.csrs.set_time.write(1)
                for _ in range(500):
                    if (yield dut.satellite.rt_packet.tsc_load):
                        loads.append((yield dut.satellite.rt_packet.tsc_load_value));break
                    yield
                else:self.fail('Serialized TSC load did not reach satellite')
                for _ in range(25):yield
                tb.now=((yield dut.tsc_master.full_ts_cri)+2048)&~7
                yield from tb.write(0,1);tb.delay(160)
                yield from tb.write(0,0);tb.delay(240)
                yield from tb.write(1,1);tb.delay(160)
                yield from tb.write(1,0)
                yield from tb.sync()
                for _ in range(40):yield
                self.assertEqual((yield dut.master.rt_controller.csrs.protocol_error.w),0)
            done[0]=True
        def watchdog():
            for _ in range(4000):
                if done[0]:return
                yield
            self.fail('Bounded master/satellite test timed out')
        run_simulation(dut,{'sys':[test(),watchdog(),tb.check_ttls(changes)]},upstream.TestFullStack.clocks)
        if underflow:self.assertEqual(changes,[])
        else:
            self.assertEqual(len(loads),1)
            self.assertEqual([ch for _,ch in changes],[0,0,1,1])
            self.assertEqual([changes[i+1][0]-changes[i][0] for i in range(3)],[20,30,20])

    def test_native_time_load_and_two_remote_outputs(self):self.exercise()
    def test_underflow_has_no_remote_edge(self):self.exercise(True)
    def test_old_local_timestamp_width_refused(self):
        pair=EncodedPair(2)
        with self.assertRaisesRegex(ValueError,'fine width3'):
            GenesysMasterBackend(rtio.TSC(glbl_fine_ts_width=0),pair.alice)

if __name__=='__main__':unittest.main()
