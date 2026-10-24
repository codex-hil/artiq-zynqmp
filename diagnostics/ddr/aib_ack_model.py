"""Offline AIB protocol reference; no MMIO or hardware admission. LGPL-3.0-or-later."""
from dataclasses import dataclass
RPU_MASTER_MASK=0x00030000

def word(v):
 return type(v) is int and 0<=v<2**32

@dataclass
class AibModel:
 boot: int
 state: str='NEW'
 mask: int=0
 request_word: int=0
 last_ack: int=0
 sequence: int=0
 polls: int=0
 budget: int=0
 def begin(self,boot,sequence,mask,request,ack,response_type,budget):
  if self.state!='NEW':raise ValueError('Model already used')
  if type(boot) is not int or boot!=self.boot or type(sequence) is not int or not 0<sequence<2**64:raise ValueError('Wrong epoch/sequence')
  if not all(word(v) for v in (mask,request,ack,response_type)) or not mask or mask&~RPU_MASTER_MASK:raise ValueError('Only reviewed RPU master subset modeled')
  if (request|ack)&mask:raise ValueError('Fresh deasserted request/ACK required')
  if type(budget) is not int or not 1<=budget<=1024:raise ValueError('Finite poll budget required')
  self.sequence=sequence;self.mask=mask;self.request_word=request|mask;self.response_type=response_type;self.budget=budget;self.state='REQUESTED_MODEL'
  return self.receipt()
 def observe(self,boot,sequence,request,ack,response_type):
  if self.state!='REQUESTED_MODEL':raise ValueError('No active polling window')
  self.polls+=1
  if type(boot) is not int or type(sequence) is not int or boot!=self.boot or sequence!=self.sequence or not all(word(v) for v in (request,ack,response_type)) or request!=self.request_word or response_type!=self.response_type:
   self.state='FAILED_HELD_MODEL'
  else:
   self.last_ack=ack
   if ack&self.mask==self.mask:self.state='DRAINED_HELD_MODEL'
   elif self.polls>=self.budget:self.state='FAILED_HELD_MODEL'
  return self.receipt()
 def release(self):
  raise ValueError('No automatic release; reviewed full restoration required')
 def receipt(self):
  return dict(kind='OFFLINE_AIB_REFERENCE_NOT_HW_ACK',state=self.state,boot=self.boot,sequence=self.sequence,mask=hex(self.mask),request_word=hex(self.request_word),polls=self.polls,budget=self.budget,last_ack=hex(self.last_ack),destructive_test_allowed=False,limits='Synthetic state only; no actual request write, elapsed-time bound, register access or path isolation proof.')
