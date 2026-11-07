"""PS AXI to native master/local RTIO candidate; LGPL-3.0-or-later."""
import sys,unittest
from pathlib import Path
from migen import passive
from migen.sim import run_simulation
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tests'))
from test_local_rtio import AXIMaster
from test_master_routing import Pair,CLOCKS
from master_csr import GenesysMasterCSR

class MasterCSRTests(unittest.TestCase):
    def make(self):
        d=Pair(now64=True);d.submodules.csr=GenesysMasterCSR(d.time,d.ki,d.master,d.routing)
        return d,AXIMaster(d.csr.axi),lambda key:d.csr.registers[key]['address']
    def test_axi_time_profile_and_local_remote_events(self):
        d,m,addr=self.make();edges=[];loads=[];done=[False]
        def run():
            self.assertEqual((yield from m.read(addr('profile_identity'))),GenesysMasterCSR.IDENTITY)
            self.assertEqual((yield from m.read(addr('profile_fine_width'))),3)
            self.assertEqual((yield from m.read(addr('profile_coarse_hz'))),125000000)
            yield from m.write(addr('kernel_counter_update'),1)
            high=yield from m.read(addr('kernel_counter'));low=yield from m.read(addr('kernel_counter')+4)
            self.assertEqual(high,0);self.assertGreater(low,0);self.assertEqual(low%8,0)
            yield from m.write(addr('master_underflow_margin'),100)
            for _ in range(25):
                if (yield from m.read(addr('master_rx_up'))):break
            else:self.fail('No encoded link')
            yield from m.write(addr('master_set_time'),1)
            yield from m.write(addr('kernel_target'),1<<24)
            yield from m.write(addr('master_o_get_buffer_space'),1)
            for _ in range(30):
                if not (yield from m.read(addr('master_o_wait'))):break
            else:self.fail('Remote buffer request timed out')
            self.assertGreater((yield from m.read(addr('master_o_dbg_buffer_space'))),0)
            base=((yield d.time.full_ts_cri)+12000)&~7
            for offset,node,value in [(0,0,1),(320,0,0),(640,1,1),(960,1,0)]:
                yield from m.write(addr('kernel_target'),node<<24)
                yield from m.write(addr('kernel_now'),0)
                yield from m.write(addr('kernel_now')+4,base+offset)
                # Actual AXI transaction latency stages the synchronous now64 CSR.
                yield from m.write(addr('kernel_o_data')+15*4,value)
                self.assertEqual((yield from m.read(addr('kernel_o_status'))),0)
            for _ in range(2200):yield
            self.assertEqual((yield from m.read(addr('master_protocol_error'))),0)
            done[0]=True
        @passive
        def monitor():
            old=[0,0];cycle=0
            while True:
                values=[(yield d.local_pad),(yield d.remote_pad)]
                for i in range(2):
                    if values[i]!=old[i]:edges.append((cycle,i,values[i]))
                if (yield d.satellite.rt_packet.tsc_load):loads.append((yield d.satellite.rt_packet.tsc_load_value))
                old=values;cycle+=1;yield
        def watchdog():
            for _ in range(6000):
                if done[0]:return
                yield
            self.fail('AXI RTIO candidate timed out')
        run_simulation(d,{'sys':[run(),monitor(),watchdog()]},CLOCKS)
        self.assertEqual(len(loads),1)
        self.assertEqual([(i,v) for _,i,v in edges],[(0,1),(0,0),(1,1),(1,0)])
        self.assertEqual(edges[1][0]-edges[0][0],40);self.assertEqual(edges[3][0]-edges[2][0],40)

    def test_address_alias_and_partial_write_slverr_then_recovery(self):
        d,m,addr=self.make();a=d.csr.axi
        def rejected(address,strb):
            yield a.aw.addr.eq(address);yield a.aw.size.eq(2);yield a.aw.burst.eq(1);yield a.aw.len.eq(0);yield a.aw.id.eq(0x1234)
            yield from m.handshake(a.aw)
            yield a.w.data.eq(0xdeadbeef);yield a.w.strb.eq(strb);yield a.w.last.eq(1)
            yield from m.handshake(a.w)
            for _ in range(100):
                if (yield a.b.valid):break
                yield
            else:self.fail('SLVERR did not complete')
            for _ in range(4):
                self.assertEqual((yield a.b.resp),2);self.assertEqual((yield a.b.id),0x1234);yield
            yield a.b.ready.eq(1);yield;yield a.b.ready.eq(0);yield
        def rejected_read(address):
            yield a.ar.addr.eq(address);yield a.ar.size.eq(2);yield a.ar.burst.eq(1);yield a.ar.len.eq(0);yield a.ar.id.eq(0x4321)
            yield from m.handshake(a.ar)
            for _ in range(100):
                if (yield a.r.valid):break
                yield
            else:self.fail('Read SLVERR did not complete')
            for _ in range(4):
                self.assertEqual((yield a.r.resp),2);self.assertEqual((yield a.r.id),0x4321);yield
            yield a.r.ready.eq(1);yield;yield a.r.ready.eq(0);yield
        def run():
            yield from m.write(addr('kernel_target'),0)
            for address,strb in [(0x9ffffffc,15),(0xa0002000,15),(0x1a0000000,15),(addr('kernel_target'),1)]:
                yield from rejected(address,strb)
                self.assertEqual((yield from m.read(addr('kernel_target'))),0)
                self.assertEqual((yield from m.read(addr('profile_identity'))),GenesysMasterCSR.IDENTITY)
            for address in [0x9ffffffc,0xa0002000,0x1a0000000]:
                yield from rejected_read(address)
                self.assertEqual((yield from m.read(addr('profile_identity'))),GenesysMasterCSR.IDENTITY)
        run_simulation(d,run(),CLOCKS)
    def test_now64_word_order_without_implicit_event(self):
        d,m,addr=self.make()
        def run():
            yield from m.write(addr('kernel_now'),0x11223344)
            yield from m.write(addr('kernel_now')+4,0x55667788)
            self.assertEqual((yield from m.read(addr('kernel_now'))),0x11223344)
            self.assertEqual((yield from m.read(addr('kernel_now')+4)),0x55667788)
            self.assertEqual((yield d.ki.now.storage),0x1122334455667788)
            self.assertEqual((yield d.local_pad),0);self.assertEqual((yield d.remote_pad),0)
        run_simulation(d,run(),CLOCKS)
    def test_old_kernel_csr_shape_refused(self):
        d=Pair()
        with self.assertRaisesRegex(ValueError,'now64'):
            GenesysMasterCSR(d.time,d.ki,d.master,d.routing)

if __name__=='__main__':unittest.main()
