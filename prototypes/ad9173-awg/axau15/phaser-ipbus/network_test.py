"""Physical IPbus checks. Caller holds the AXAU15 lease; DDS stays muted."""
import json,time
from client import Phaser

def probe(output):
 c=Phaser()
 try:
  identity=c.identify();c.mute(True)
  before=c.read(5)[0]
  values=[(0x12345678+i*0x10203)&0xffffffff for i in range(200)]
  c.write(4,values,increment=False)
  assert c.read(4)[0]==values[-1]
  assert c.read(5)[0]==(before+200)&0xffffffff
  for address in [0,0x200,0xdead]:
   result=c.transact(1,address,[1],allow_error=True)
   assert result[1]&15,result
  assert c.transact(0,0xdead,allow_error=True)[1]&15
  commits=[]
  for i in range(20):
   commits.append(c.configure([[(-1e6-i*1000,.5,0)],[(1e6+i*1000,.25,.25)]]))
  c.configure([[(-1e6,.5,0)],[(1e6,.5,0)]])
  assert c.read(0x10)[0]==511
  assert c.read(0x1a)[0]==0
  data={'status':'PHYSICAL_NATIVE_IPBUS_PASS','identity':identity,'nonincrementing_writes':200,'negative_bus_errors':4,'commits':commits,'counters':c.read(0x18,3),'read_retries':c.read_retry_events,'final_mute':c.read(0x13)[0]}
  (output/'network.json').write_text(json.dumps(data,indent=2)+'\n')
  return data
 finally:c.close()
