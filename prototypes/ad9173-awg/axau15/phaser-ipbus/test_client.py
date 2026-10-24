#!/usr/bin/env python3
"""Loopback UDP loss/reordering regression; never accesses the PM12 network."""
import socket,struct,threading,collections
from client import Client
s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);s.bind(('127.0.0.1',0));s.settimeout(.05)
stop=threading.Event();counts=collections.Counter();first=None
def server():
 global first
 while not stop.is_set():
  try:data,peer=s.recvfrom(4096)
  except socket.timeout:continue
  w=struct.unpack('>'+str(len(data)//4)+'I',data);kind=(w[1]>>4)&15;addr=w[2];counts[(kind,addr)]+=1
  if kind not in [0,2] or addr==3:continue
  if addr==0 and counts[(kind,addr)]==1:first=w;continue
  if addr==0 and first:s.sendto(struct.pack('>III',first[0],first[1]&~15,0xbad),peer)
  if addr==2:s.sendto(b'bad',peer);continue
  n=(w[1]>>8)&255;s.sendto(struct.pack('>'+str(2+n)+'I',w[0],w[1]&~15,*[0xdead0000+(i if kind==0 else 0) for i in range(n)]),peer)
t=threading.Thread(target=server);t.start();c=Client('127.0.0.1',s.getsockname()[1]);c.s.settimeout(.05)
try:
 assert c.read(0)==[0xdead0000] and counts[(0,0)]==2 and len(c.read_retry_events)==1
 assert c.read(1,3,False)==[0xdead0000]*3
 for kind in [1,4]:
  try:c.transact(kind,1,[0,1] if kind==4 else [1]);raise AssertionError('expected timeout')
  except TimeoutError:pass
  assert counts[(kind,1)]==1,'write/RMW must never be retried'
 try:c.read(2);raise AssertionError('expected malformed reply rejection')
 except RuntimeError:pass
 assert counts[(0,2)]==1
 try:c.read(3);raise AssertionError('expected bounded read timeout')
 except TimeoutError:pass
 assert counts[(0,3)]==3
 print('PASS local UDP dropped read/stale reply/nonincrementing read,bounded read retries,no write/RMW retries,malformed reply rejection')
finally:c.close();stop.set();t.join(timeout=1);s.close()
