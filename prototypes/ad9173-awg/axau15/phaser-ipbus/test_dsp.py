import env
import numpy as np
from migen import *
from dsp import Generator,WORDS
from registers import Registers,MAGIC

class DUT(Module):
 def __init__(self):
  self.submodules.dsp=Generator()
  self.submodules.regs=Registers(self.dsp)

def test_registers_and_dds():
 d=DUT();r=d.regs;wave=[];errors=[]
 def access(addr,value=None,fail=False):
  yield r.address.eq(addr);yield r.write.eq(value is not None);yield r.wdata.eq(value or 0);yield r.strobe.eq(1)
  for _ in range(20):
   yield
   if (yield r.ack):break
  else:raise AssertionError('bus timeout')
  assert bool((yield r.err))==fail
  answer=(yield r.rdata)
  yield r.strobe.eq(0)
  for _ in range(3):yield
  return answer
 def control():
  assert (yield from access(0))==MAGIC
  yield from access(0,1,True)
  yield from access(0xdead,fail=True)
  yield from access(0x114,0x80000000,True)
  # +Fs/64 on CH0, -Fs/32 on CH1, amplitude0.5. Phase offset90deg CH1.
  yield from access(0x100,0x04000000)
  yield from access(0x101,0x40000000)
  yield from access(0x10a,0xf8000000)
  yield from access(0x10b,0x40004000)
  yield from access(0x114,0x103)
  yield from access(0x14,1)
  assert (yield r.busy)
  yield from access(0x100,0x12345678,True)
  for _ in range(100):
   yield
   if not (yield r.busy):break
  else:raise AssertionError('commit timeout')
  assert (yield from access(0x200))==0x04000000
  assert (yield from access(0x12))==1
  yield from access(0x13,0)
  for _ in range(200):yield
  yield from access(0x13,1)
  for _ in range(50):yield
 def sample():
  for cycle in range(1500):
   yield
   row=[]
   for ch in d.dsp.samples:
    v=[]
    for i,q in ch:v.append(complex((yield i),(yield q)))
    row.append(v)
   wave.append(row)
 run_simulation(d,{'sys':control(),'jesd':sample()},clocks={'sys':10,'jesd':6})
 a=np.array(wave)
 # Identify the contiguous enabled interval; avoid start/end pipelines.
 active=np.flatnonzero(abs(a[:,0,0])>1000)
 assert len(active)>100
 for ch,step in [(0,2*np.pi/64),(1,-2*np.pi/32)]:
  v=a[active[20]:active[-20],ch,:].flatten()
  assert np.max(abs(abs(v)-16382))<8
  error=np.angle(v[1:]*np.conj(v[:-1]))-step
  assert np.max(abs(error))<.0003
 assert np.max(abs(a[-20:]))==0

def samples_for(tones):
 d=Generator();result=[]
 words=[0]*WORDS
 for k,(ftw,phase,amp) in enumerate(tones):words[2*k]=ftw&0xffffffff;words[2*k+1]=(amp&65535)<<16|phase
 words[-1]=0x101
 value=sum(w<<(32*i) for i,w in enumerate(words))
 def net():
  yield d.held.eq(value);yield d.request.eq(1);yield d.mute.eq(0)
  for _ in range(500):yield
 def read():
  for n in range(400):
   yield
   if n>80:
    for i,q in d.samples[0]:result.append(complex((yield i),(yield q)))
 run_simulation(d,{'sys':net(),'jesd':read()},clocks={'sys':10,'jesd':6})
 return np.array(result)

def test_phase_and_five_tone_sum():
 a=samples_for([(0x04000000,0,4096)])
 b=samples_for([(0x04000000,16384,4096)])
 assert np.max(abs(b-1j*a))<4
 tones=[(i*0x02000000,0,2048) for i in range(1,6)]
 v=samples_for(tones)
 # Independent spectral fit: all five configured complex bins, correct amplitude.
 t=np.arange(len(v));mat=np.column_stack([np.exp(2j*np.pi*i*t/128) for i in range(1,6)])
 coeff=np.linalg.lstsq(mat,v,rcond=None)[0]
 assert np.max(abs(abs(coeff)-2048))<5
 assert np.sqrt(np.mean(abs(v-mat@coeff)**2))<5

def test_saturation_does_not_wrap():
 v=samples_for([(0x04000000,0,16384)]*5)
 assert np.max(v.real)==32767 and np.min(v.real)==-32768
 assert np.max(v.imag)==32767 and np.min(v.imag)==-32768
 # With all phases aligned, the clipped waveform has the same sign as a single tone.
 ref=samples_for([(0x04000000,0,4096)])
 mask=abs(ref.real)>100
 assert np.all(v.real[mask]*ref.real[mask]>0)
