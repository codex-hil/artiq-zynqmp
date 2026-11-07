"""Same-link native master AUX/RT simulation; LGPL-3.0-or-later."""
import unittest
from migen import passive
from migen.sim import run_simulation
from artiq.gateware.drtio.aux_controller import DRTIOAuxController
from master_aux import GenesysMasterAux
from test_master_routing import Pair,CLOCKS

class MasterAuxTests(unittest.TestCase):
    controller_type=DRTIOAuxController
    def exercise(self,count,traffic=False,rx_phase=0):
        d=Pair();d.submodules.master_aux=GenesysMasterAux(d.master,controller_type=self.controller_type)
        d.submodules.satellite_aux=self.controller_type(d.satellite.link_layer)
        ma,sa=d.master_aux.controller,d.satellite_aux
        self.assertIs(d.master_aux.link_layer,d.master.link_layer)
        done=[False];edges=[];overlap=[False];received=[]
        def wait(csr,value,limit=700):
            for _ in range(limit):
                if bool((yield from csr.read()))==value:return
                yield
            self.fail('Bounded AUX status timeout')
        def receive(aux,words,index):
            yield from wait(aux.receiver.aux_rx_present,True)
            ptr=yield from aux.receiver.aux_read_pointer.read()
            self.assertEqual(ptr,index%8)
            actual=[]
            for j in range(len(words)):actual.append((yield from aux.bus.read((8192+ptr*1024)//4+j)))
            self.assertEqual(actual,words);received.append((index,len(words)))
            self.assertEqual((yield from aux.receiver.aux_rx_error.read()),0)
            yield from aux.receiver.aux_rx_present.write(1)
            for _ in range(8):yield
        def send(aux,words):
            for i,w in enumerate(words):yield from aux.bus.write(i,w)
            yield from aux.transmitter.aux_tx_length.write(4*len(words))
            yield from aux.transmitter.aux_tx.write(1)
            yield
        def rt_write(timestamp,value):
            yield from d.ki.target.write(1<<24)
            yield from d.ki.now_hi.write(timestamp>>32)
            yield from d.ki.now_lo.write(timestamp&0xffffffff)
            yield
            yield from d.ki.o_data.write(value)
            yield
            for _ in range(100):
                s=yield from d.ki.o_status.read()
                self.assertEqual(s&6,0)
                if s==0:return
                yield
            self.fail('RT command stuck')
        def run():
            yield from wait(d.master.link_layer.rx_up,True)
            yield from wait(d.satellite.link_layer.rx_up,True)
            for _ in range(20):yield
            if traffic:
                yield from d.master.rt_controller.csrs.underflow_margin.write(100)
                yield from d.master.rt_controller.csrs.o_get_buffer_space.write(1)
                yield
                yield from wait(d.master.rt_controller.csrs.o_wait,False)
            for n in range(count):
                size=64 if traffic else (1,3,17)[n%3]
                words=[((n+1)*0x01020304 ^ j*0x07654321)&0xffffffff for j in range(size)]
                yield from send(ma,words)
                if traffic:
                    base=((yield d.time.full_ts_cri)+4096)&~7
                    yield from rt_write(base,1);yield from rt_write(base+160,0)
                yield from wait(ma.transmitter.aux_tx,False)
                yield from receive(sa,words,n)
                reply=[x^0x55aa55aa for x in words]
                yield from send(sa,reply)
                yield from wait(sa.transmitter.aux_tx,False)
                yield from receive(ma,reply,n)
            if traffic:
                for _ in range(800):yield
            self.assertEqual((yield d.master.rt_controller.csrs.protocol_error.w),0)
            done[0]=True
        @passive
        def monitor():
            previous=0;cycle=0
            while True:
                if (yield d.master.link_layer.tx_aux_frame) and (yield d.master.link_layer.tx_rt_frame):overlap[0]=True
                v=yield d.remote_pad
                if v!=previous:edges.append((cycle,v));previous=v
                cycle+=1;yield
        def watchdog():
            for _ in range(6000):
                if done[0]:return
                yield
            self.fail('AUX/RT session timeout')
        clocks=dict(CLOCKS);clocks['rtio_rx']=(8,rx_phase) if rx_phase else 8
        run_simulation(d,{'sys':[run(),monitor(),watchdog()]},clocks)
        self.assertEqual(len(received),2*count)
        if traffic:
            self.assertTrue(overlap[0]);self.assertEqual([v for _,v in edges],[1,0]);self.assertEqual(edges[1][0]-edges[0][0],20)
        else:self.assertEqual(edges,[])
    def test_bidirectional_ring_wrap(self):self.exercise(9)
    def test_rt_frames_and_aux_share_native_link(self):self.exercise(1,True)
    def test_receive_phase_offset(self):self.exercise(1,rx_phase=2)
    def test_duplicate_and_cross_clock_attachment_refused(self):
        d=Pair()
        with self.assertRaisesRegex(ValueError,'one control/TX clock'):GenesysMasterAux(d.master,control_clock='ps',tx_clock='gth_tx')
        GenesysMasterAux(d.master)
        with self.assertRaisesRegex(ValueError,'already owns'):GenesysMasterAux(d.master)
if __name__=='__main__':unittest.main()
