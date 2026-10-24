"""Native IPbus2 client for the CERN controller; requests are never emulated."""
import socket,struct,time,json,array,statistics
from pathlib import Path
class Client:
 def __init__(self,host='192.168.2.241',port=50001,order='>'):
  self.s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);self.s.connect((host,port));self.s.settimeout(1);self.order=order;self.tid=0;self.read_retry_events=[]
 def transact(self,kind,address,values=None,count=1,allow_error=False):
  assert 1<=count<=255
  header=0x20000000|((self.tid&4095)<<16)|(count<<8)|(kind<<4)|15;self.tid=(self.tid+1)&4095
  request=[0x200000f0,header,address]+list(values or [])
  self.s.send(struct.pack(self.order+str(len(request))+'I',*request));deadline=time.monotonic()+2
  while time.monotonic()<deadline:
   data=self.s.recv(4096)
   if len(data)%4:raise RuntimeError('unaligned IPbus reply')
   words=list(struct.unpack(self.order+str(len(data)//4)+'I',data))
   if len(words)<2 or words[0]!=request[0] or (words[1]&0xffff00f0)!=(header&0xffff00f0):continue
   error=words[1]&15
   if error and not allow_error:raise RuntimeError('IPbus bus error '+str(error)+' at '+hex(address))
   if not error and (words[1]&0xffffff00)!=(header&0xffffff00):raise RuntimeError('IPbus count mismatch')
   return words if allow_error else words[2:]
  raise TimeoutError('No matching transaction')
 def read(self,address,count=1,increment=True):
  # Register and frozen-memory reads have no side effects. Writes/RMW/ARM
  # are never automatically retried; a lost write reply stays an error.
  for attempt in range(3):
   try:return self.transact(0 if increment else 2,address,count=count)
   except TimeoutError:
    self.read_retry_events.append({'address':address,'count':count,'attempt':attempt})
    if attempt==2:raise
 def write(self,address,values,increment=True):return self.transact(1 if increment else 3,address,values,count=len(values))
 def block(self,address,count):
  data=[]
  for i in range(0,count,128):data+=self.read(address+i,min(128,count-i))
  return data
 def close(self):self.s.close()

FS=307200000
MAGIC=0x41585048
class Phaser(Client):
 def identify(self):
  magic,abi,fs,tones=self.read(0,4)
  if (magic,fs,tones)!=(MAGIC,FS,5) or abi not in (0x10000,0x10001):raise RuntimeError('Wrong Phaser endpoint/ABI')
  return {'magic':magic,'abi':abi,'sample_rate':fs,'tones':tones}
 def configure(self,channels,enable=3,rephase=True):
  """channels: two lists of up to five (Hz, amplitude[-1,1), phase turns)."""
  identity=self.identify()
  if identity['abi']>=0x10001 and self.read(0x20)[0]:raise RuntimeError('Envelope playback owns DDS configuration')
  if len(channels)!=2 or enable not in range(4):raise ValueError('Two channels and enable0..3 required')
  words=[]
  for channel in channels:
   if len(channel)>5:raise ValueError('At most five tones')
   for frequency,amplitude,phase in list(channel)+[(0,0,0)]*(5-len(channel)):
    if not -FS/2<=frequency<FS/2 or not -1<=amplitude<1:raise ValueError('Frequency/amplitude outside range')
    ftw=round(frequency/FS*2**32)&0xffffffff
    asf=round(amplitude*32768)
    if not -32768<=asf<=32767:raise ValueError('Rounded amplitude outside range')
    pow=round(phase*65536)&65535
    words.extend([ftw,((asf&65535)<<16)|pow])
  words.append(enable|(int(rephase)<<8))
  if self.read(0x11)[0]:raise RuntimeError('Previous commit pending')
  old=self.read(0x12)[0]
  self.write(0x100,words)
  if self.read(0x100,21)!=words:raise RuntimeError('Shadow readback mismatch')
  self.write(0x14,[1])
  end=time.monotonic()+2
  while time.monotonic()<end:
   if not self.read(0x11)[0] and self.read(0x12)[0]==((old+1)&0xffffffff):break
  else:raise TimeoutError('DDS commit acknowledgement missing')
  if self.read(0x200,21)!=words:raise RuntimeError('Committed readback mismatch')
  return self.read(0x12)[0]
 def mute(self,muted=True):self.identify();self.write(0x13,[int(muted)])
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--host',default='192.168.2.241');p.add_argument('--tone',action='store_true');p.add_argument('--mute',action='store_true');p.add_argument('--config',type=Path,help='JSON: two arrays of [Hz,amplitude,phase_turns]');p.add_argument('--keep-phase',action='store_true');a=p.parse_args()
 import fcntl
 lease=open('/home/codex-hil/.cache/alinx-210512180081.lock','a+')
 fcntl.flock(lease,fcntl.LOCK_EX|fcntl.LOCK_NB)
 c=Phaser(a.host)
 try:
  print(json.dumps(c.identify(),indent=2))
  if a.config:c.configure(json.loads(a.config.read_text()),rephase=not a.keep_phase);c.mute(False)
  if a.tone:c.configure([[(-1e6,.5,0)],[(1e6,.5,0)]]);c.mute(False)
  if a.mute:c.mute(True)
 finally:c.close()
