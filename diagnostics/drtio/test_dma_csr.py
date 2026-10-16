"""Real PS AXI/CSR control, native decoder and bounded AXI memory; LGPL-3.0-or-later.

The CRI target is controlled status only. Actual SED/TTL has separate tests.
"""
import sys
from pathlib import Path
import unittest
from migen import Module,ClockDomain,passive
from migen.sim import run_simulation
from migen.genlib.resetsync import AsyncResetSynchronizer
from litex.soc.interconnect.axi import AXIInterface
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'boards/genesys_zu-5ev/1_gateware'))
sys.path.insert(0,str(ROOT/'tests'))
from test_zynqmp_dma import AXIMemorySim,encode_sequence
from test_aux_ps import FunctionalReset
from aux_ps import AuxPS
from dma_csr import DMACSR

class CSRDriver:
    def __init__(self,test,bus,regs):self.test,self.bus,self.regs=test,bus,regs
    def wait(self,s):
        for _ in range(200):
            if (yield s):return
            yield
        self.test.fail('PS AXI transaction timed out')
    def read_word(self,addr):
        a=self.bus
        yield a.ar.addr.eq(addr);yield a.ar.id.eq(7);yield a.ar.size.eq(2)
        yield a.ar.len.eq(0);yield a.ar.burst.eq(1);yield a.ar.valid.eq(1)
        yield from self.wait(a.ar.ready);yield;yield a.ar.valid.eq(0)
        yield from self.wait(a.r.valid)
        self.test.assertEqual((yield a.r.resp),0)
        self.test.assertEqual((yield a.r.id),7)
        data=(yield a.r.data)
        yield a.r.ready.eq(1);yield;yield a.r.ready.eq(0);yield
        return data
    def write_word(self,addr,value):
        a=self.bus
        yield a.aw.addr.eq(addr);yield a.aw.id.eq(5);yield a.aw.size.eq(2)
        yield a.aw.len.eq(0);yield a.aw.burst.eq(1);yield a.aw.valid.eq(1)
        yield from self.wait(a.aw.ready);yield;yield a.aw.valid.eq(0)
        yield a.w.data.eq(value);yield a.w.strb.eq(15);yield a.w.last.eq(1);yield a.w.valid.eq(1)
        yield from self.wait(a.w.ready);yield;yield a.w.valid.eq(0)
        yield from self.wait(a.b.valid)
        self.test.assertEqual((yield a.b.resp),0)
        yield a.b.ready.eq(1);yield;yield a.b.ready.eq(0);yield
    def write(self,name,value):
        r=self.regs['dma_'+name]
        for i in range(r['words']):
            yield from self.write_word(r['address']+4*i,(value>>(32*(r['words']-i-1)))&0xffffffff)
    def read(self,name):
        r=self.regs['dma_'+name];value=0
        for i in range(r['words']):value=(value<<32)|(yield from self.read_word(r['address']+4*i))
        return value
    def pending(self):
        for _ in range(200):
            if (yield from self.read('pending')):return
        self.test.fail('No stable DMA result')

class DMACSRTests(unittest.TestCase):
    def exercise(self,mode):
        d=Module();d.clock_domains.cd_rtio_rx=ClockDomain('rtio_rx')
        bus=AXIInterface(data_width=64,address_width=49,id_width=6)
        d.submodules.control=c=DMACSR(bus,arena_base=0,arena_size=4096)
        d.submodules.ps=p=AuxPS(extra_banks=[('dma',4,c.csrs)])
        driver=CSRDriver(self,p.axi,c.memory_map(p.BASE+4*0x800)['registers'])
        trace=encode_sequence([(0,32,0,1),(0,64,0,0)],8)
        words=trace+[0]*(64-len(trace))+trace
        if mode in ('watchdog','budget'):words=[0x0101010101010101]*1024
        memory=AXIMemorySim(bus,words,max_queue=3)
        ar=[];last=[]
        @passive
        def monitor():
            while True:
                if (yield bus.ar.valid) and (yield bus.ar.ready):ar.append((yield bus.ar.addr))
                if (yield bus.r.valid) and (yield bus.r.ready) and (yield bus.r.last):last.append(1)
                yield
        def configure(watch=100000):
            yield from driver.write('address',0)
            yield from driver.write('time_offset',0x1234567800000000)
            yield from driver.write('max_bursts',16)
            yield from driver.write('watchdog',watch)
        def run():
            yield c.fault.eq(0);yield c.engine.cri.o_status.eq(0)
            yield from configure(100 if mode=='watchdog' else 100000)
            self.assertEqual((yield from driver.read('time_offset')),0x1234567800000000)
            if mode=='reject':
                for name,value,flag in [('address',64,2),('address',0x100000000,4),('max_bursts',0,8),('watchdog',0,16)]:
                    yield from configure();yield from driver.write(name,value)
                    yield from driver.write('start',1)
                    self.assertTrue((yield from driver.read('reject'))&flag)
                    self.assertEqual((yield from driver.read('accepted')),0)
                    self.assertFalse(ar)
                    yield from driver.write('clear',1)
                yield from configure();yield c.fault.eq(1)
                yield from driver.write('start',1)
                self.assertTrue((yield from driver.read('reject'))&32)
                self.assertFalse(ar)
                return
            if mode=='budget':yield from driver.write('max_bursts',4)
            if mode=='snapshot':yield c.engine.cri.o_status.eq(2)
            if mode=='busy':yield c.engine.cri.o_status.eq(1)
            yield from driver.write('start',1)
            if mode=='busy':
                yield from driver.write('clear',1)
                self.assertEqual((yield from driver.read('active')),1)
                yield from driver.write('address',512)
                yield from driver.write('start',1)
                self.assertTrue((yield from driver.read('reject'))&1)
                self.assertEqual((yield from driver.read('accepted')),1)
                self.assertEqual((yield c.engine.guard.reader.base_address.storage),0)
                yield c.engine.cri.o_status.eq(0)
            yield from driver.pending()
            result=(yield from driver.read('result_error'))
            self.assertEqual(result,4 if mode=='snapshot' else 33 if mode=='watchdog' else 65 if mode=='budget' else 0)
            if mode=='snapshot':
                self.assertEqual((yield from driver.read('result_timestamp')),0x1234567800000020)
            self.assertEqual(len(ar),len(last))
            self.assertLessEqual(len(ar),16)
            self.assertTrue(all(a+128<=2048 for a in ar))
            self.assertEqual((yield from driver.read('accepted')),1)
            self.assertEqual((yield from driver.read('completed')),1)
            # Pending result cannot be overwritten by a new start.
            yield from driver.write('start',1)
            self.assertTrue((yield from driver.read('reject'))&64)
            self.assertEqual((yield from driver.read('accepted')),1)
            # Acknowledgement permits a fresh, bounded trace after any failure.
            yield from driver.write('clear',1)
            yield c.engine.cri.o_status.eq(0)
            memory.data=words[:64]+trace+[0]*64
            yield from driver.write('address',512)
            yield from driver.write('watchdog',100000)
            yield from driver.write('max_bursts',16)
            yield from driver.write('start',1)
            yield from driver.pending()
            self.assertEqual((yield from driver.read('result_error')),0)
            self.assertEqual((yield from driver.read('accepted')),2)
            self.assertEqual((yield from driver.read('completed')),2)
            self.assertEqual(len(ar),len(last))
        run_simulation(d,{'sys':[run(),monitor(),memory.ar(),memory.r()]},
            clocks={'sys':10,'rtio_rx':(13,2),'dma_write':10,'dma_read':(13,2),
                    'gth_rx':8,'gth_tx':(11,3),'aux_sys':10,'aux_rx':8,'aux_tx':(11,3)},
            special_overrides={AsyncResetSynchronizer:FunctionalReset})
    def test_ps_axi_multiword_snapshot_and_result_ack(self):self.exercise('snapshot')
    def test_preflight_rejects_without_memory_access(self):self.exercise('reject')
    def test_watchdog_abort_drains_and_next_trace_recovers(self):self.exercise('watchdog')
    def test_missing_terminator_bounded_reads_and_recovery(self):self.exercise('budget')

    def test_busy_start_and_clear_do_not_mutate_active_epoch(self):self.exercise('busy')
