# SPDX-License-Identifier: LGPL-3.0-or-later
import unittest
from types import SimpleNamespace
from migen import Signal,Instance
from migen.genlib.resetsync import AsyncResetSynchronizer
from master_gth_adapter import MasterGTHAdapter

class GTHAdapterTests(unittest.TestCase):
    def make(self,width=20):
        pads=SimpleNamespace(**{name:Signal() for name in ('rxp','rxn','txp','txn')})
        ref=SimpleNamespace(p=Signal(),n=Signal())
        clock,reset=Signal(),Signal()
        return MasterGTHAdapter(pads,ref,clock,reset,Signal(width)),clock,reset
    def test_freerun_clock_and_external_link_configuration(self):
        d,clock,reset=self.make()
        f=d.get_fragment()
        instances=[s for s in f.specials if isinstance(s,Instance)]
        self.assertEqual(len(instances),4)
        gt=next(s for s in instances if s.of=='drtio_gth')
        inputs={item.name:item.expr for item in gt.items if isinstance(item,Instance.Input)}
        self.assertIs(inputs['gtwiz_reset_clk_freerun_in'],clock)
        self.assertIs(inputs['drpclk_in'],clock)
        self.assertIs(inputs['gtwiz_reset_all_in'],reset)
        for name in ('loopback_in','rxprbssel_in','txprbssel_in'):
            self.assertEqual(inputs[name].value,0)
        self.assertEqual(sum(isinstance(s,AsyncResetSynchronizer) for s in f.specials),1)
        self.assertEqual({cd.name for cd in f.clock_domains},{'gt_align'})
    def test_aligner_clears_on_readiness_loss_and_reacquires(self):
        from migen import Module
        from migen.sim import run_simulation
        from protocol_probe import COMMAS
        from test_master_ps_cdc import FunctionalReset
        class EmptyPhysicalInstance:
            @staticmethod
            def lower(special):return Module()
        d,clock,reset=self.make()
        def test():
            yield d.raw_status.rxpma.eq(1)
            yield d.raw_status.rxdone.eq(1)
            yield d.raw_status.rxactive.eq(1)
            yield d.rx_unaligned.eq(COMMAS[0])
            for _ in range(6):yield
            self.assertEqual((yield d.aligner.aligned),1)
            self.assertEqual((yield d.aligner.offset),0)
            yield d.raw_status.rxpma.eq(0)
            yield d.rx_unaligned.eq(0)
            for _ in range(4):yield
            self.assertEqual((yield d.aligner.aligned),0)
            yield d.raw_status.rxpma.eq(1)
            for _ in range(4):yield
            self.assertEqual((yield d.aligner.aligned),0)
            yield d.rx_unaligned.eq(COMMAS[0]<<3)
            for _ in range(6):yield
            self.assertEqual((yield d.aligner.aligned),1)
            self.assertEqual((yield d.aligner.offset),3)
        # Physical instances intentionally removed. Only fabric alignment/reset
        # logic is modeled, with a functional reset override and ideal RX clock.
        run_simulation(d,{'gt_align':test()},clocks={'gt_align':8},
            special_overrides={Instance:EmptyPhysicalInstance,
                               AsyncResetSynchronizer:FunctionalReset})

    def test_non_raw20_refused(self):
        with self.assertRaises(ValueError):self.make(32)

if __name__=='__main__':unittest.main()
