"""Actual Migen DMA completion under AXI/CRI backpressure. LGPL-3.0-or-later."""
import unittest
from migen import Module, passive, run_simulation
from litex.soc.interconnect.axi import AXIInterface
from test_zynqmp_dma import dma, encode_sequence, reverse_word
from artiq.gateware.rtio import cri

REPORTS=[]


class DrainTB(Module):
 def __init__(self):
  self.bus=AXIInterface(data_width=64,address_width=49,id_width=6)
  self.submodules.dut=dma.DMA(self.bus)


class DrainTests(unittest.TestCase):
 def scenario(self,delay,cri_delay,response,trigger):
  tb=DrainTB();bus=tb.bus;dut=tb.dut
  writes=[(i,100+i,0,i+1) for i in range(12)]
  data=encode_sequence(writes,8)
  queue=[];stats=dict(ar=0,last=0,peak=0,busy_seen=False,completed=False,r_stall=0,ar_stall=0)
  @passive
  def address():
   while True:
    ready=len(queue)<12
    yield bus.ar.ready.eq(ready)
    yield
    if ready and (yield bus.ar.valid):queue.append(((yield bus.ar.addr),(yield bus.ar.len)))
  @passive
  def reply():
   while True:
    if not queue:yield;continue
    addr,length=queue.pop(0)
    for beat in range(length+1):
     for _ in range(delay):yield
     index=addr//8+beat
     value=data[index] if index<len(data) else 0
     yield bus.r.data.eq(reverse_word(value,64))
     yield bus.r.resp.eq(response);yield bus.r.last.eq(beat==length);yield bus.r.valid.eq(1)
     yield
     while not (yield bus.r.ready):yield
     yield bus.r.valid.eq(0);yield
  @passive
  def rtio():
   while True:
    if (yield dut.cri.cmd)==cri.commands['write']:
     yield dut.cri.o_status.eq(1)
     for _ in range(cri_delay):yield
     yield dut.cri.o_status.eq(0)
    yield
  @passive
  def monitor():
   while True:
    if (yield bus.ar.valid) and (yield bus.ar.ready):stats['ar']+=1
    if (yield bus.r.valid) and (yield bus.r.ready) and (yield bus.r.last):stats['last']+=1
    if (yield bus.r.valid) and not (yield bus.r.ready):stats['r_stall']+=1
    if (yield bus.ar.valid) and not (yield bus.ar.ready):stats['ar_stall']+=1
    outstanding=stats['ar']-stats['last']
    self.assertGreaterEqual(outstanding,0);self.assertLess(outstanding,128)
    stats['peak']=max(stats['peak'],outstanding)
    yield
  def stimulus():
   yield from dut.dma.base_address.write(0)
   yield from dut.enable.write(trigger)
   yield
   for cycle in range(20000):
    busy=(yield dut.enable.w)
    stats['busy_seen']|=bool(busy)
    if stats['busy_seen'] and not busy:
     self.assertEqual(stats['ar'],stats['last'])
     self.assertGreater(stats['ar'],0)
     self.assertEqual((yield bus.ar.valid),0)
     self.assertEqual((yield bus.r.valid),0)
     self.assertEqual((yield dut.dma.wb_reader.bus_error.status),int(response!=0))
     stats['completed']=True
     # No trigger writer: IDLE must stay quiet after the completed run.
     prior=stats['ar']
     for _ in range(30):
      yield
      self.assertEqual((yield dut.enable.w),0);self.assertEqual(stats['ar'],prior)
     break
    yield
   else:self.fail('DMA drain timeout')
  run_simulation(tb,[stimulus(),address(),reply(),rtio(),monitor()])
  self.assertTrue(stats['completed'])
  REPORTS.append(dict(delay=delay,cri_delay=cri_delay,response=response,trigger=trigger,**stats))
 def test_drain_and_zero_trigger(self):
  for delay in (0,3,17):
   for cri_delay in (0,31):
    for response in (0,2):
     for trigger in (0,1):
      with self.subTest(delay=delay,cri_delay=cri_delay,response=response,trigger=trigger):
       self.scenario(delay,cri_delay,response,trigger)


if __name__=='__main__':unittest.main()
