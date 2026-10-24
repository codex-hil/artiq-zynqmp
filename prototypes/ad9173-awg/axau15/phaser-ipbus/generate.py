import env
import argparse,os,json,importlib.util,re
from pathlib import Path
from types import SimpleNamespace
from migen import *
from migen.fhdl import verilog
from migen.fhdl.specials import READ_FIRST
from migen.genlib.cdc import MultiReg
from litex.build.xilinx.common import xilinx_special_overrides
from litex.soc.cores.clock import USPMMCM
from liteeth.mac.core import LiteEthMACCore
from dsp import Generator
from envelope import EnvelopePlayer, EnvelopeStage
from registers import Registers
from rgmii import PHY
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('jesd_target',HERE.parent/'jesd-probe/generate.py');base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
class Top(base.AXAU15):
 def __init__(self):
  super().__init__(streaming=True)
  self.submodules.generator=dsp=Generator()
  self.submodules.envelope=player=EnvelopePlayer()
  self.submodules.envelope_stage=stage=EnvelopeStage(dsp.samples,player)
  for inputs,samples in zip(self.link.converter_inputs,stage.samples):
   self.comb += [inputs[0].eq(Cat(*[iq[0] for iq in samples])),inputs[1].eq(Cat(*[iq[1] for iq in samples]))]
  self.clock_domains.cd_net=ClockDomain('net')
  self.submodules.net_cm=cm=USPMMCM(speedgrade=-2,name="net_cm_mmcm")
  cm.clkfbout_mult_frange=(2,65,1);cm.clkout0_divide_range=(2,129,1)
  cm.register_clkin(ClockSignal('sys'),100e6);cm.create_clkout(self.cd_net,125e6)
  pads=SimpleNamespace(**{name:Signal(width,name='eth_'+name) for name,width in [('rx_clk',1),('rx_ctl',1),('rx_data',4),('tx_clk',1),('tx_ctl',1),('tx_data',4),('rst_n',1),('mdc',1),('mdio',1)]})
  self.ios.update(vars(pads).values())
  pins=Signal(4);mdi=Signal();startup=Signal(22,reset=2500000)
  self.sync += If(startup!=0,startup.eq(startup-1))
  self.comb += [pads.rst_n.eq((startup==0)&~pins[3]),pads.mdc.eq(pins[0])]
  self.specials += Instance('IOBUF',i_I=pins[1],i_T=~pins[2],o_O=mdi,io_IO=pads.mdio)
  self.submodules.phy=phy=PHY(pads,self.cd_net.clk,ResetSignal('net'))
  self.submodules.mac=mac=ClockDomainsRenamer({'sys':'net'})(LiteEthMACCore(phy,dw=8,with_sys_datapath=True,with_store_and_forward=True))
  self.submodules.registers=regs=ClockDomainsRenamer('net')(Registers(dsp,player))
  status=Signal(9);self.specials += MultiReg(self.jesd_status,status,'net');self.comb += regs.status.eq(status)
  rx,tx=mac.source,mac.sink;first=Signal(reset=1)
  self.sync.net += If(tx.valid&tx.ready,first.eq(tx.last))
  self.comb += [rx.ready.eq(1),tx.first.eq(first),tx.be.eq(1)]
  got_ip=Signal()
  self.specials += Instance('rng_ipbus_endpoint',i_mac_clk=self.cd_net.clk,i_rst_macclk=self.cd_net.rst,i_ipb_clk=self.cd_net.clk,i_rst_ipb=self.cd_net.rst,
   i_mac_rx_data=rx.data,i_mac_rx_valid=rx.valid,i_mac_rx_last=rx.last&rx.valid,i_mac_rx_error=rx.error&rx.valid,
   o_mac_tx_data=tx.data,o_mac_tx_valid=tx.valid,o_mac_tx_last=tx.last,o_mac_tx_error=tx.error,i_mac_tx_ready=tx.ready,
   i_mac_addr=0x02000000a115,i_ip_addr=0xc0a802f1,o_got_ip=got_ip,
   o_ipb_addr=regs.address,o_ipb_wdata=regs.wdata,o_ipb_strobe=regs.strobe,o_ipb_write=regs.write,i_ipb_rdata=regs.rdata,i_ipb_ack=regs.ack,i_ipb_err=regs.err)
  self.sync.net += [If(rx.valid&rx.last,regs.rx_frames.eq(regs.rx_frames+1)),If(tx.valid&tx.ready&tx.last,regs.tx_frames.eq(regs.tx_frames+1)),If(rx.valid&rx.error,regs.rx_errors.eq(regs.rx_errors+1))]
  self.specials += Instance('eth_scan',i_status=Cat(cm.locked,got_ip,regs.rx_frames[0],regs.tx_frames[0]),i_mdi=mdi,o_pins=pins)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',required=True,type=Path);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True);os.chdir(a.output)
 dut=Top();fragment=dut.get_fragment()
 # Capture data (not only the address) on the receiving clock. FIFO pointer
 # ownership excludes read/write collision; read-first enables true BRAM inference.
 memories=[m for m in fragment.specials if isinstance(m,Memory) and m.width==12 and m.depth==32]
 if len(memories)!=2:raise RuntimeError('Expected two Ethernet CDC memories')
 for memory in memories:
  for port in memory.ports:
   if port.dat_r is not None:
    assert not port.async_read and port.we is None
    port.mode=READ_FIRST
 v=verilog.convert(fragment,ios=dut.ios,name='axau15_jesd',special_overrides=xilinx_special_overrides)
 # Real dual-clock BRAM for MAC CDC FIFOs; avoid distributed RAM data crossing.
 v.main_source,n=re.subn(r'(reg \[11:0\] storage_\d+\[0:31\];)',r'(* ram_style = "block" *) \1',v.main_source)
 if n!=2:raise RuntimeError('Expected two Ethernet CDC memories')
 v.main_source,n=re.subn(r'(reg \[95:0\] envelope_ram\[0:255\];)',r'(* ram_style = "block" *) \1',v.main_source)
 if n!=1:raise RuntimeError('Expected envelope RAM')
 v.write('axau15_jesd.v')
 Path('target.json').write_text(json.dumps({'device':'xcau15p-ffvb676-2-i','tones_per_channel':5,'sample_rate':307200000,'ip':'192.168.2.241','mac':'02:00:00:00:a1:15','physical':'NOT_RUN'},indent=2)+'\n')
