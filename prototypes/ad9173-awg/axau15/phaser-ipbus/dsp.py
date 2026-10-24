"""Phaser MultiToneDDS, two complex samples/cycle, atomic shared configuration.
Not MIQRO/Fastlink/DRTIO. FTWs use307.2MS/s, not Phaser250MS/s.
"""
import env
from migen import *
from migen.genlib.cdc import MultiReg
from dds import MultiToneDDS
TONES=5
WORDS=2*TONES*2+1
class Generator(Module):
 def __init__(self):
  self.held=Signal(WORDS*32,name='config_held')
  self.request=Signal(name='config_request')
  self.ack=Signal(name='config_ack')
  self.active=Signal(WORDS*32,name='config_active')
  self.active.attr.add('dont_touch')  # Keep atomic CDC bank outside DSP input registers.
  self.mute=Signal(reset=1)
  self.samples=[]
  req=Signal();muted=Signal(reset=1)
  self.specials += [MultiReg(self.request,req,'jesd'),MultiReg(self.mute,muted,'jesd')]
  pending=Signal();settle=Signal(6);clear=Signal(3)
  self.sync.jesd += [
   If((req!=self.ack)&~pending,
    self.active.eq(self.held),pending.eq(1),settle.eq(32),
    clear.eq(Mux(self.held[20*32+8],4,0))
   ).Elif(pending,
    If(settle!=0,settle.eq(settle-1)).Else(self.ack.eq(req),pending.eq(0))),
   If(clear!=0,clear.eq(clear-1))]
  # Give incoming clear command priority over counter decrement.
  self.sync.jesd += If((req!=self.ack)&~pending,clear.eq(Mux(self.held[20*32+8],4,0)))
  for ch in range(2):
   d=ClockDomainsRenamer('jesd')(MultiToneDDS(2,TONES,32,16,16,16,True))
   setattr(self.submodules,'dds'+str(ch),d)
   for tone,bank in enumerate(d.reg_banks):
    offset=(ch*TONES+tone)*64
    f,p,a,c=[pair[0] for pair in bank]
    self.comb += [f.eq(self.active[offset:offset+32]),p.eq(self.active[offset+32:offset+48]),
     a.eq(self.active[offset+48:offset+64]),c.eq(clear!=0)]
   output=[]
   for source in d.sources:
    i=Signal((16,True));q=Signal((16,True));output.append((i,q))
    self.sync.jesd += [i.eq(Mux(~muted & ~pending & self.active[20*32+ch],source.i,0)),
                          q.eq(Mux(~muted & ~pending & self.active[20*32+ch],source.q,0))]
   self.samples.append(output)
