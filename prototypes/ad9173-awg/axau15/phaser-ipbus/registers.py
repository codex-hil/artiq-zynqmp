"""IPbus2 register frontend. Side effects once per ACK, including held strobes."""
import env
from migen import *
from migen.genlib.cdc import MultiReg
from dsp import WORDS
MAGIC=0x41585048
class Registers(Module):
 def __init__(self,dsp,envelope=None):
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
  envelope_busy=Signal()
  if envelope is not None:
   self.env_length=Signal(9,reset=1,name='env_config_length')
   self.env_repeats=Signal(32,reset=1,name='env_config_repeats')
   self.env_command=Signal(2,name='env_config_command')
   self.env_request=Signal();self.env_abort_request=Signal()
   env_ack=Signal();abort_ack=Signal();env_mode=Signal();env_playing=Signal();env_armed=Signal();env_arm_id=Signal(30);env_result=Signal(2)
   env_previous=Signal();env_commands=Signal(32)
   self.specials += [MultiReg(envelope.ack,env_ack),MultiReg(envelope.abort_ack,abort_ack),
                     MultiReg(envelope.mode,env_mode),MultiReg(envelope.playing,env_playing),
                     MultiReg(envelope.result,env_result),MultiReg(envelope.armed_status,env_armed),MultiReg(envelope.arm_id,env_arm_id)]
   self.comb += [envelope.command.eq(self.env_command),envelope.length.eq(self.env_length),
                 envelope.repeats.eq(self.env_repeats),envelope.request.eq(self.env_request),
                 envelope.abort_request.eq(self.env_abort_request),
                 envelope_busy.eq((self.env_request!=env_ack)|(self.env_abort_request!=abort_ack)),
                 envelope.write_address.eq(addr[:10])]
   self.sync += [env_previous.eq(env_ack),If(env_previous!=env_ack,env_commands.eq(env_commands+1))]
  self.sync += uptime.eq(uptime+1)
  value=Signal(32);valid=Signal();writable=Signal();bad=Signal()
  cases={0:[value.eq(MAGIC)],1:[value.eq(0x10002 if envelope is not None else 0x10000)],2:[value.eq(307200000)],3:[value.eq(5)],
    4:[value.eq(scratch),writable.eq(1)],5:[value.eq(writes)],6:[value.eq(uptime[:32])],7:[value.eq(uptime[32:])],
    0x10:[value.eq(self.status)],0x11:[value.eq(self.busy)],0x12:[value.eq(self.commits)],
    0x13:[value.eq(self.mute),writable.eq(1),bad.eq(wd>1)],
    0x14:[value.eq(0),writable.eq(1),bad.eq((wd!=1)|self.busy|envelope_busy)],
    0x18:[value.eq(self.rx_frames)],0x19:[value.eq(self.tx_frames)],0x1a:[value.eq(self.rx_errors)]}
  if envelope is not None:
   cases.update({
    8:[value.eq(3)],
    0x20:[value.eq(envelope_busy)],
    0x21:[value.eq(Cat(env_mode,env_playing,Constant(0,2),env_result))],
    0x22:[value.eq(env_commands)],
    0x23:[value.eq(self.env_length),writable.eq(1),bad.eq(envelope_busy|(wd==0)|(wd>256))],
    0x24:[value.eq(self.env_repeats),writable.eq(1),bad.eq(envelope_busy|(wd==0))],
    0x25:[value.eq(0),writable.eq(1),bad.eq(envelope_busy|self.busy|((wd!=1)&(wd!=2)&(wd!=3)))],
    0x27:[value.eq(env_armed)],
    0x28:[value.eq(env_arm_id)],
    0x26:[value.eq(self.env_abort_request!=abort_ack),writable.eq(1),bad.eq((wd!=1)|(self.env_abort_request!=abort_ack))],
   })
  for i,s in enumerate(self.shadow):
   cases[0x100+i]=[value.eq(s),writable.eq(1),bad.eq(self.busy | (((wd&~0x103)!=0) if i==WORDS-1 else 0))]
  # Held image is immutable until acknowledgement, useful readback of committed data.
  for i in range(WORDS):cases[0x200+i]=[value.eq(self.held[i*32:(i+1)*32])]
  self.comb += [value.eq(0),valid.eq(1),writable.eq(0),bad.eq(0),Case(addr,{**cases,'default':valid.eq(0)})]
  memory_window=(addr>=0x400)&(addr<0x800)
  if envelope is not None:
   self.comb += If(memory_window,value.eq(envelope.read_data),valid.eq(1),writable.eq(1),
                  bad.eq(envelope_busy|((addr[:2]==3)&(wd!=0))))
  fail=~valid | (wr & (~writable|bad))
  actions={4:scratch.eq(wd),0x13:self.mute.eq(wd[0]),0x14:[self.held.eq(Cat(*self.shadow)),self.request.eq(~self.request)]}
  for i,s in enumerate(self.shadow):actions[0x100+i]=s.eq(wd)
  if envelope is not None:
   actions.update({0x23:self.env_length.eq(wd),0x24:self.env_repeats.eq(wd),
                   0x25:[self.env_command.eq(wd),self.env_request.eq(~self.env_request)],
                   0x26:self.env_abort_request.eq(~self.env_abort_request)})
  fire=Signal()
  if envelope is not None:
   self.comb += [envelope.write_enable.eq(fire&memory_window&(addr[:2]!=3)),envelope.write_data.eq(wd)]
  self.sync += If(fire,writes.eq(writes+1),Case(addr,actions))
  self.submodules.fsm=f=FSM(reset_state='IDLE')
  f.act('IDLE',If(self.strobe,NextValue(addr,self.address),NextValue(wd,self.wdata),NextValue(wr,self.write),If((self.address>=0x400)&(self.address<0x800)&~self.write,NextState('MEMORY_WAIT')).Else(NextState('COMPLETE'))))
  f.act('MEMORY_WAIT',NextState('COMPLETE'))
  f.act('COMPLETE',NextValue(self.ack,1),NextValue(self.err,fail),NextValue(self.rdata,value),fire.eq(wr&~fail),NextState('ACK'))
  f.act('ACK',NextValue(self.ack,0),NextValue(self.err,0),NextState('IDLE'))
