# SPDX-License-Identifier: LGPL-3.0-or-later
"""Negative controls using a small independent AW/W pairing target, not real CSR."""
import unittest
from migen import Module,Signal,If,ClockDomain,ClockDomainsRenamer
from migen.sim import run_simulation
from litex.soc.interconnect.axi import AXIInterface
from master_axi_drain import MasterAXIDrain

class PairingTarget(Module):
    def __init__(self):
        self.axi=a=AXIInterface(data_width=32,address_width=40,id_width=16)
        self.aw_full=aw=Signal();self.w_full=w=Signal()
        self.commits=Signal(4);self.address=Signal(40);self.data=Signal(32)
        self.comb += [a.aw.ready.eq(~aw),a.w.ready.eq(~w),a.b.valid.eq(aw&w),a.b.resp.eq(0)]
        self.sync += [If(a.aw.valid&a.aw.ready,aw.eq(1),self.address.eq(a.aw.addr)),
                      If(a.w.valid&a.w.ready,w.eq(1),self.data.eq(a.w.data)),
                      If(aw&w,If(self.commits==0,self.commits.eq(1)))]

class NegativeResetTests(unittest.TestCase):
    def exercise(self,first,reset_side):
        d=Module()
        d.clock_domains.cd_bridge=ClockDomain('bridge')
        d.clock_domains.cd_target=ClockDomain('target')
        d.submodules.target=t=ClockDomainsRenamer('target')(PairingTarget())
        d.submodules.bridge=b=ClockDomainsRenamer('bridge')(MasterAXIDrain(t.axi))
        a=b.axi
        def cycles(n):
            for _ in range(n):yield
        def send(name):
            ch=getattr(a,name)
            yield ch.valid.eq(1);yield
            for _ in range(20):
                if (yield ch.ready):break
                yield
            else:self.fail('channel not accepted')
            yield;yield ch.valid.eq(0);yield
        def test():
            yield b.stop.eq(0);yield
            yield a.aw.addr.eq(0xa0000010);yield a.aw.size.eq(2)
            yield a.w.data.eq(68);yield a.w.last.eq(1);yield a.w.strb.eq(15)
            yield from send(first);yield from cycles(8)
            self.assertEqual((yield getattr(t,first+'_full')),1)
            self.assertEqual((yield t.commits),0)
            # Deliberately violate the coordinated reset contract in this fixture.
            for name in (('bridge','target') if reset_side=='both' else (reset_side,)):
                yield getattr(d,'cd_'+name).rst.eq(1)
            yield from cycles(5)
            for name in (('bridge','target') if reset_side=='both' else (reset_side,)):
                yield getattr(d,'cd_'+name).rst.eq(0)
            yield from cycles(5)
            yield b.stop.eq(0);yield
            yield a.aw.addr.eq(0xa0000020);yield a.w.data.eq(12)
            other='w' if first=='aw' else 'aw'
            yield from send(other)
            if reset_side=='both':
                yield from send(first)
            yield from cycles(12)
            if reset_side=='bridge':
                # New complementary half combines with old half retained in target.
                self.assertEqual((yield t.commits),1)
                self.assertEqual((yield t.address),0xa0000010 if first=='aw' else 0xa0000020)
                self.assertEqual((yield t.data),12 if first=='aw' else 68)
                self.assertEqual((yield a.b.valid),1)
            elif reset_side=='both':
                self.assertEqual((yield t.commits),1)
                self.assertEqual((yield t.address),0xa0000020)
                self.assertEqual((yield t.data),12)
                self.assertEqual((yield a.b.valid),1)
            else:
                # Bridge remembers first half as sent, target forgot it: stuck.
                self.assertEqual((yield t.commits),0)
                self.assertEqual((yield getattr(t,first+'_full')),0)
                self.assertEqual((yield getattr(t,other+'_full')),1)
                self.assertEqual((yield b.idle),0)
                self.assertEqual((yield a.b.valid),0)
                self.assertEqual((yield getattr(a,first).ready),0)
        run_simulation(d,{'bridge':test()},clocks={'bridge':8,'target':8})
    def test_aw_bridge_reset_stale_address_mix(self):self.exercise('aw','bridge')
    def test_w_bridge_reset_stale_data_mix(self):self.exercise('w','bridge')
    def test_aw_target_reset_loses_address_stalls(self):self.exercise('aw','target')
    def test_w_target_reset_loses_data_stalls(self):self.exercise('w','target')
    def test_aw_both_reset_fresh_pair_only(self):self.exercise('aw','both')
    def test_w_both_reset_fresh_pair_only(self):self.exercise('w','both')
if __name__=='__main__':unittest.main()
