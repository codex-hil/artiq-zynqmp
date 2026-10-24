"""IPbus2 register frontend. Side effects once per ACK, including held strobes."""
import env
from migen import *
from migen.genlib.cdc import MultiReg
from dsp import WORDS
MAGIC=0x41585048
class Registers(Module):
 def __init__(self,dsp):
  self.address=Signal(32);self.wdata=Signal(32);self.strobe=Signal();self.write=Signal()
  self.rdata=Signal(32);self.ack=Signal();self.err=Signal()
  self.status=Signal(32);self.rx_frames=Signal(32);self.tx_frames=Signal(32);self.rx_errors=Signal(32)
  self.shadow=[Signal(32,name=f'shadow_{i}') for i in range(WORDS)]
  self.held=Signal(WORDS*32,name='config_held');self.request=Signal(name='config_request')
  self.busy=Signal();self.commits=Signal(32);self.mute=Signal(reset=1)
  ack=Signal();self.specials += MultiReg(dsp.ack,ack)
  self.comb += [dsp.held.eq(self.held),dsp.request.eq(self.request),dsp.mute.eq(self.mute),self.busy.eq(self.request!=ack)]
  previous=Signal();self.sync += [previous.eq(ack),If(previous!=ack,self.commits.eq(self.commits+1))]
  addr=Signal(32);wd=Signal(32);wr=Signal();scratch=Signal(32);writes=Signal(32);uptime=Signal(64)
  self.sync += uptime.eq(uptime+1)
  value=Signal(32);valid=Signal();writable=Signal();bad=Signal()
  cases={0:[value.eq(MAGIC)],1:[value.eq(0x10000)],2:[value.eq(307200000)],3:[value.eq(5)],
    4:[value.eq(scratch),writable.eq(1)],5:[value.eq(writes)],6:[value.eq(uptime[:32])],7:[value.eq(uptime[32:])],
    0x10:[value.eq(self.status)],0x11:[value.eq(self.busy)],0x12:[value.eq(self.commits)],
    0x13:[value.eq(self.mute),writable.eq(1),bad.eq(wd>1)],
    0x14:[value.eq(0),writable.eq(1),bad.eq((wd!=1)|self.busy)],
    0x18:[value.eq(self.rx_frames)],0x19:[value.eq(self.tx_frames)],0x1a:[value.eq(self.rx_errors)]}
  for i,s in enumerate(self.shadow):
   cases[0x100+i]=[value.eq(s),writable.eq(1),bad.eq(self.busy | (((wd&~0x103)!=0) if i==WORDS-1 else 0))]
  # Held image is immutable until acknowledgement, useful readback of committed data.
  for i in range(WORDS):cases[0x200+i]=[value.eq(self.held[i*32:(i+1)*32])]
  self.comb += [value.eq(0),valid.eq(1),writable.eq(0),bad.eq(0),Case(addr,{**cases,'default':valid.eq(0)})]
  fail=~valid | (wr & (~writable|bad))
  actions={4:scratch.eq(wd),0x13:self.mute.eq(wd[0]),0x14:[self.held.eq(Cat(*self.shadow)),self.request.eq(~self.request)]}
  for i,s in enumerate(self.shadow):actions[0x100+i]=s.eq(wd)
  fire=Signal()
  self.sync += If(fire,writes.eq(writes+1),Case(addr,actions))
  self.submodules.fsm=f=FSM(reset_state='IDLE')
  f.act('IDLE',If(self.strobe,NextValue(addr,self.address),NextValue(wd,self.wdata),NextValue(wr,self.write),NextState('COMPLETE')))
  f.act('COMPLETE',NextValue(self.ack,1),NextValue(self.err,fail),NextValue(self.rdata,value),fire.eq(wr&~fail),NextState('ACK'))
  f.act('ACK',NextValue(self.ack,0),NextValue(self.err,0),NextState('IDLE'))
