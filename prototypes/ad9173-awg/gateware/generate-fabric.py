"""Laboratory GTGREFCLK reference via HMC SCLKOUT13 / FMC LA00.
No persistent programming. Internal DAC NCO settings are untouched by this image.
"""
import json
from pathlib import Path
from importlib import import_module
from migen import *
from litex.gen import Reduce
from migen.fhdl import verilog
from migen.genlib.cdc import MultiReg
from litex.build.xilinx.common import xilinx_special_overrides
from liteiclink.serdes.gth4_ultrascale import GTH4,GTH4QuadPLL
DualLink=import_module('generate-link').DualLink
class FabricTX(Module):
 def __init__(self,with_spi=False,subclass=1,phy_prbs7=False,native_8b10b=False,hd=1,native_prbs7=False,slow_6144=False):
  assert not ((phy_prbs7 or native_prbs7) and native_8b10b)
  self.ref_p=Signal(name='ref_p');self.ref_n=Signal(name='ref_n');refraw=Signal();refclk=Signal()
  self.specials += [Instance('IBUFDS',p_DIFF_TERM='TRUE',i_I=self.ref_p,i_IB=self.ref_n,o_O=refraw),Instance('BUFG',i_I=refraw,o_O=refclk)]
  self.clock_domains.cd_sys=ClockDomain('sys');osc=Signal();eos=Signal()
  self.specials += [Instance('STARTUPE3',o_CFGMCLK=osc,o_EOS=eos,i_GSR=0,i_GTS=0,i_KEYCLEARB=1,i_PACK=0,i_USRCCLKO=0,i_USRCCLKTS=1,i_USRDONEO=1,i_USRDONETS=0,i_DO=0,i_DTS=15,i_FCSBO=1,i_FCSBTS=1),Instance('BUFG',i_I=osc,o_O=self.cd_sys.clk)]
  self.comb += self.cd_sys.rst.eq(~eos)
  payload_amp=Signal(16,reset=0x2000,name='payload_amp')
  ref_freq=245.76e6 if slow_6144 else 184.32e6;line_rate=6.144e9 if slow_6144 else 7.3728e9
  qpll=GTH4QuadPLL(refclk,ref_freq,line_rate,refclk_from_fabric=True);self.submodules.qpll=qpll;self.pll_config=qpll.config
  phys=[];ios={self.ref_p,self.ref_n}
  for n in range(4):
   tx=Record([('p',1),('n',1)],name=f'tx{n}');rx=Record([('p',1),('n',1)])
   gth=GTH4(qpll,tx,rx,100e6,data_width=40,tx_buffer_enable=True,rx_buffer_enable=True,clock_aligner=False,pll_master=n==0)
   if phy_prbs7:self.comb += gth.tx_prbs_config.eq(1)
   gth.n=n;gth.add_stream_endpoints();gth=ClockDomainsRenamer({'tx':f'jesd_phy{n}_tx','rx':f'jesd_phy{n}_rx'})(gth)
   if native_prbs7:gth.gth_params.update(i_TXPRBSSEL=1,i_TXPRBSFORCEERR=0)
   if slow_6144:
    prbs_sel=Signal();self.specials+=MultiReg(payload_amp[15],prbs_sel,f'jesd_phy{n}_tx');gth.gth_params.update(i_TXPRBSSEL=prbs_sel,i_TXPRBSFORCEERR=0)
   gth.gth_params.update(i_TX8B10BEN=int(native_8b10b),i_TX8B10BBYPASS=0)
   if native_8b10b:gth.gth_params.update(i_TXDATA=gth.sink.data,i_TXCTRL0=0,i_TXCTRL1=0,i_TXCTRL2=gth.sink.ctrl)
   setattr(self.submodules,f'gt{n}',gth);self.comb += [gth.rx_enable.eq(0),rx.p.eq(0),rx.n.eq(0)];phys.append(gth);ios.update(tx.flatten())
  self.clock_domains.cd_jesd=ClockDomain('jesd');self.comb += [self.cd_jesd.clk.eq(phys[0].cd_tx.clk),self.cd_jesd.rst.eq(ResetSignal('jesd_phy0_tx'))]
  link=DualLink(phys,subclass=subclass,hd=hd,did=0x61 if slow_6144 else 0);self.submodules.link=link
  sync=[]
  for n in range(2):
   pads=Record([('p',1),('n',1)],name=f'sync{n}');s=Signal();self.specials += Instance('IBUFDS',p_DIFF_TERM='TRUE',i_I=pads.p,i_IB=pads.n,o_O=s);ios.update(pads.flatten());sync.append(s)
  ready=Signal();self.specials+=MultiReg(Reduce('AND',[p.tx_ready for p in phys]),ready,'jesd')
  self.comb += [link.jsync.eq(Cat(sync[0],sync[1])),link.jref.eq(0),link.enable.eq(ready)]
  if not with_spi:self.comb+=payload_amp.eq(0x2000)
  link.drive_payload(payload_amp,self)
  # Counts and states exposed on USER1 without PS/USB-SPI ownership changes.
  txcount=Signal(32);self.sync.jesd+=txcount.eq(txcount+1)
  refcount=Signal(32);syscount=Signal(32);self.clock_domains.cd_ref=ClockDomain('ref',reset_less=True);self.comb+=self.cd_ref.clk.eq(refclk)
  self.sync.ref += refcount.eq(refcount+1);self.sync += syscount.eq(syscount+1)
  self.led=Signal(name='led');self.comb+=self.led.eq(syscount[25]);ios.add(self.led)
  capture=Signal();shift=Signal();drck=Signal();sel=Signal();tdi=Signal();scan=Signal(160)
  self.specials += Instance('BSCANE2',p_JTAG_CHAIN=1,o_CAPTURE=capture,o_SHIFT=shift,o_DRCK=drck,o_SEL=sel,o_TDI=tdi,i_TDO=scan[0])
  self.clock_domains.cd_scan=ClockDomain('scan',reset_less=True);self.comb+=self.cd_scan.clk.eq(drck)
  debug=[link.enable,ResetSignal('jesd'),*[c.enable for c in link.cores],*[c.jsync for c in link.cores],*[c.lmfc.zero for c in link.cores],*[c.links[0].reset for c in link.cores]]
  for c in link.cores:
   debug += [c.links[0].fsm.ongoing(state) for state in ['SEND-CGS','SEND-ILAS','SEND-DATA']]
  flags=Signal(32);self.comb+=flags.eq(Cat(qpll.lock,*[p.tx_ready for p in phys],link.ready,link.jsync,*debug,payload_amp[15],Constant(0,6)))
  self.sync.scan += If(sel,If(capture,scan.eq(Cat(refcount,syscount,flags,txcount,Constant(0xfabc204b,32)))).Elif(shift,scan.eq(Cat(scan[1:],tdi))))
  if with_spi:
   sck=Signal(name='sck');mosi=Signal(name='mosi');miso=Signal(name='miso');cs_dac=Signal(name='cs_dac');cs_clock=Signal(name='cs_clock');spi_en=Signal(name='spi_en')
   self.specials+=Instance('spi_console',i_clk=ClockSignal('sys'),i_spi_en=spi_en,i_miso=miso,o_sck=sck,o_mosi=mosi,o_cs_dac=cs_dac,o_cs_clock=cs_clock,o_payload_amp=payload_amp)
   ios.update([sck,mosi,miso,cs_dac,cs_clock,spi_en])
  self.ios=ios
if __name__=='__main__':
 import argparse
 parser=argparse.ArgumentParser();parser.add_argument('--hd',type=int,choices=[0,1],default=1);parser.add_argument('--spi-console',action='store_true');parser.add_argument('--phy-prbs7',action='store_true');parser.add_argument('--native-8b10b',action='store_true');parser.add_argument('--native-prbs7',action='store_true');parser.add_argument('--slow-6144',action='store_true');parser.add_argument('--subclass',type=int,choices=[0,1],default=1);args=parser.parse_args()
 r=Path(__file__).resolve().parent;d=FabricTX(args.spi_console,args.subclass,args.phy_prbs7,args.native_8b10b,args.hd,args.native_prbs7,args.slow_6144);verilog.convert(d,ios=d.ios,name='fabric_jesd_tx',special_overrides=xilinx_special_overrides).write(str(r/'fabric_jesd_tx.v'));(r/'fabric-qpll-config.json').write_text(json.dumps(d.pll_config,indent=2)+'\n')
