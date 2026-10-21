from importlib import import_module
from migen import *
from migen.sim import run_simulation
from litejesd204.link import LiteJESD204BLinkTX
settings_for=import_module('generate-link').settings_for

def test_ilas_configuration():
 for link in range(2):
  for lane in range(2):
   assert settings_for(link).get_configuration_data(lane)==[0,link,lane,0x81,1,31,1,15,0x2f,0x20,0x80,0,0,0x44+link+lane]

def test_cgs_ilas_data_and_resynchronization():
 class DUT(Module):
  def __init__(self):
   self.lanes=[]
   for link in range(2):
    for lane in range(2):
     tx=LiteJESD204BLinkTX(32,settings_for(link),lane);self.submodules+=tx;self.lanes.append(tx)
 dut=DUT()
 def generator():
  for tx in dut.lanes:
   yield tx.reset.eq(1);yield tx.jsync.eq(0);yield tx.lmfc_zero.eq(1);yield tx.sink.data.eq(0x76543210)
  yield
  for tx in dut.lanes:yield tx.reset.eq(0)
  for cycle in range(20):
   yield
   for tx in dut.lanes:
    assert (yield tx.source.data)==0xbcbcbcbc
    assert (yield tx.source.ctrl)==15
    assert not (yield tx.ready)
  # Only link0 receives SYNC: link1 must remain at CGS.
  for tx in dut.lanes[:2]:yield tx.jsync.eq(1)
  observed=[[] for tx in dut.lanes]
  for cycle in range(80):
   yield
   for i,tx in enumerate(dut.lanes):
    observed[i].append(((yield tx.source.data),(yield tx.source.ctrl)))
   for tx in dut.lanes[2:]:assert not (yield tx.ready)
  for i,tx in enumerate(dut.lanes[:2]):
   assert (yield tx.ready)
   words=observed[i]
   # Four complete64-byte ILAS multiframes, each begins /R/ and ends /A/.
   starts=[n for n,(data,ctrl) in enumerate(words) if ctrl&1 and data&255==0x1c]
   assert len(starts)==4
   assert [n-starts[0] for n in starts]==[0,16,32,48]
   for start in starts:
    data,ctrl=words[start+15];assert ctrl&8 and data>>24==0x7c
   # Second ILAS multiframe contains /Q/ then the correct AD9173 config.
   octets=[]
   for data,ctrl in words[starts[1]:starts[1]+4]:octets.extend(data.to_bytes(4,'little'))
   assert octets[1]==0x9c
   assert octets[2:16]==settings_for(0).get_configuration_data(i)
  # Persistent low SYNC must return link0 to CGS.
  for tx in dut.lanes[:2]:yield tx.jsync.eq(0)
  for _ in range(12):yield
  for tx in dut.lanes[:2]:
   assert not (yield tx.ready);assert (yield tx.source.data)==0xbcbcbcbc
  # Both links can start independently and recover.
  for tx in dut.lanes:yield tx.jsync.eq(1)
  observed=[[] for tx in dut.lanes]
  for _ in range(80):
   yield
   for i,tx in enumerate(dut.lanes):
    observed[i].append(((yield tx.source.data),(yield tx.source.ctrl)))
  for i,tx in enumerate(dut.lanes):
   assert (yield tx.ready)
   words=observed[i]
   starts=[n for n,(data,ctrl) in enumerate(words) if ctrl&1 and data&255==0x1c]
   assert len(starts)==4
   octets=[]
   for data,ctrl in words[starts[1]:starts[1]+4]:octets.extend(data.to_bytes(4,'little'))
   assert octets[2:16]==settings_for(i//2).get_configuration_data(i%2)
 run_simulation(dut,generator())

def test_subclass0_configuration():
 for link in range(2):
  for lane in range(2):
   assert settings_for(link,0).get_configuration_data(lane)==[0,link,lane,0x81,1,31,1,15,0x0f,0x20,0x80,0,0,0x43+link+lane]

def test_hd0_diagnostic_configuration():
 for link in range(2):
  for lane in range(2):
   assert settings_for(link,0,0).get_configuration_data(lane)==[0,link,lane,0x81,1,31,1,15,0x0f,0x20,0,0,0,0x42+link+lane]

def test_slow6144_fresh_ilas_identity_and_clock_plan():
 from liteiclink.serdes.gth4_ultrascale import GTH4QuadPLL
 for link in range(2):
  for lane in range(2):
   assert settings_for(link,0,1,0x61).get_configuration_data(lane)==[0x61,link,lane,0x81,1,31,1,15,0x0f,0x20,0x80,0,0,0xa4+link+lane]
 config=GTH4QuadPLL.compute_config(245760000,6144000000)
 assert (config['n'],config['m'],config['d'],config['qpll'])==(100,2,2,'qpll1')
 assert 4915200000/(8*2)*16*(10/8)==config['linerate']


def test_payload_reaches_both_transport_inputs():
 # Exercise the same wrapper connection used by FabricTX. Directly driving
 # core.sink is overridden by the wrapper's external converter ports.
 DualLink=import_module('generate-link').DualLink
 dut=Module();dut.submodules.link=DualLink(subclass=0,hd=1,did=0x61)
 for name in ['sys','jesd']+[f'jesd_phy{i}_tx' for i in range(4)]:
  setattr(dut.clock_domains,'cd_'+name,ClockDomain(name))
 amplitude=Signal(16)
 dut.link.drive_payload(amplitude,dut)
 def generator():
  for value in [0x2020,0x1010,0,0x5a82]:
   yield amplitude.eq(value)
   for _ in range(3):yield
   for core in dut.link.cores:
    assert (yield core.sink.converter0)==value|(value<<16)
    assert (yield core.sink.converter1)==0
    assert (yield core.transport.source.lane0)==int.from_bytes(value.to_bytes(2,'big')*2,'little')
    assert (yield core.transport.source.lane1)==0
 run_simulation(dut,generator(),clocks={'sys':10,'jesd':10,**{f'jesd_phy{i}_tx':10 for i in range(4)}})

def test_dual_wrapper_enters_data_with_nonzero_payload():
 module=import_module('generate-link')
 dut=Module();phys=[module.PHY(i) for i in range(4)]
 dut.submodules.link=module.DualLink(phys=phys,subclass=0,hd=1,did=0x61)
 for name in ['sys','jesd']+[f'jesd_phy{i}_tx' for i in range(4)]:setattr(dut.clock_domains,'cd_'+name,ClockDomain(name))
 amp=Signal(16,reset=0x2020);dut.link.drive_payload(amp,dut)
 def generator():
  for p in phys:yield p.sink.ready.eq(1)
  yield dut.link.enable.eq(1)
  for _ in range(30):yield
  yield dut.link.jsync.eq(3)
  for _ in range(200):yield
  assert (yield dut.link.ready)==3
  for p in phys:assert (yield p.sink.valid)
 run_simulation(dut,generator(),clocks={'sys':10,'jesd':10,**{f'jesd_phy{i}_tx':10 for i in range(4)}})
