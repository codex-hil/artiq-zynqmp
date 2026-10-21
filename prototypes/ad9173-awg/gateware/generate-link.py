"""Two JESD204B mode3 TX links, L2/M2/F2/S1/NP16/K32 each.
Pure link/transport RTL only: GTH and coherent reference integration remain separate.
"""
from pathlib import Path
from migen import *
from migen.fhdl import verilog
from litex.build.xilinx.common import xilinx_special_overrides
from litex.soc.interconnect import stream
from litejesd204.common import JESD204BSettings,JESD204BPhysicalSettings,JESD204BTransportSettings,JESD204BConfigurationData
from litejesd204.core import LiteJESD204BCoreTX
class AD9173Settings(JESD204BSettings):
 def get_configuration_data(self,lid=0,debug=False):
  cd=JESD204BConfigurationData(super().get_configuration_data(lid))
  cd.hd=self.hd;cd.chksum=0
  cd.chksum=cd.get_checksum()
  octets=cd.get_octets()
  # JESD204B HD is bit7 of config octet10; upstream currently places it at5.
  octets[10]=(octets[10]&0x1f)|(cd.hd<<7)
  return octets
def settings_for(link,subclass=1,hd=1,did=0):
 settings=AD9173Settings(JESD204BPhysicalSettings(l=2,m=2,n=16,np=16),JESD204BTransportSettings(f=2,s=1,k=32,cs=0),did=did,bid=link)
 settings.hd=hd
 settings.phy.subclassv=subclass
 return settings
class PHY(Module):
 def __init__(self,n):
  self.n=n;self.sink=stream.Endpoint([('data',32),('ctrl',4)]);self.source=stream.Endpoint([('data',32),('ctrl',4)])
class DualLink(Module):
 def __init__(self,phys=None,subclass=1,hd=1,did=0):
  self.enable=Signal(name='enable');self.jsync=Signal(2,name='jsync');self.jref=Signal(name='jref');self.ready=Signal(2,name='ready');self.ios={self.enable,self.jsync,self.jref,self.ready};self.cores=[];self.converter_inputs=[]
  for link in range(2):
   phy=[PHY(2*link+i) for i in range(2)] if phys is None else phys[2*link:2*link+2]
   settings=settings_for(link,subclass,hd,did)
   core=LiteJESD204BCoreTX(phy,settings,converter_data_width=32);setattr(self.submodules,'link'+str(link),core);self.cores.append(core)
   sync_in=Signal();self.comb += sync_in.eq(self.jsync[link]);core.register_jsync(sync_in);core.register_jref(self.jref)
   self.comb += [core.enable.eq(self.enable),self.ready[link].eq(core.ready)]
   inputs=[];self.converter_inputs.append(inputs)
   for c in range(2):
    data=Signal(32,name=f'link{link}_converter{c}');self.ios.add(data);inputs.append(data);self.comb += getattr(core.sink,'converter'+str(c)).eq(data)
   for i,p in enumerate(phy):
    data=Signal(32,name=f'lane{2*link+i}_data');ctrl=Signal(4,name=f'lane{2*link+i}_ctrl');self.ios.update([data,ctrl]);self.comb += [data.eq(p.sink.data),ctrl.eq(p.sink.ctrl)]
 def drive_payload(self,amplitude,parent):
  for inputs in self.converter_inputs:
   parent.comb += [inputs[0].eq(Cat(amplitude,amplitude)),inputs[1].eq(0)]
if __name__=='__main__':
 d=DualLink();verilog.convert(d,ios=d.ios,name='jesd_dual_link',special_overrides=xilinx_special_overrides).write(str(Path(__file__).with_name('jesd_dual_link.v')))
