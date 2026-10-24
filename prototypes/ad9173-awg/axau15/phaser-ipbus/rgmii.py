"""AXAU15 JL2121 RGMII, 1Gb/s only; PHY strap supplies RX/TX2ns delays.
Adapted LiteEth Ultrascale RX/TX path (BSD2, upstream us.py). No FPGA delay
is added to data. RX MMCM compensates clock insertion. TX clock comes from local125MHz MMCM, independent of PHY RX clock.
"""
import env
from migen import *
from migen.genlib.resetsync import AsyncResetSynchronizer
from litex.soc.interconnect import stream
from litex.soc.cores.clock import USPMMCM
from liteeth.common import eth_phy_description
from liteeth.phy.parallel.rgmii.us import LiteEthPHYRGMIITX
class PHY(Module):
 dw=8;tx_clk_freq=125e6;rx_clk_freq=125e6
 def __init__(self,pads,netclk,reset):
  self.clock_domains.cd_eth_tx=ClockDomain('eth_tx');self.clock_domains.cd_eth_rx=ClockDomain('eth_rx')
  self.comb += self.cd_eth_tx.clk.eq(netclk)
  rxclk=Signal()
  self.specials += [Instance('IBUF',i_I=pads.rx_clk,o_O=rxclk),
   AsyncResetSynchronizer(self.cd_eth_tx,reset),
   Instance('ODDRE1',i_C=netclk,i_SR=0,i_D1=1,i_D2=0,o_Q=pads.tx_clk)]
  # Deskew the input clock distribution; direct BUFG insertion consumes the
  # PHY's ~2ns data eye. A -90deg (2ns) MMCM phase advance compensates insertion.
  self.submodules.rx_cm=rx_cm=USPMMCM(speedgrade=-2,name="rx_cm_mmcm")
  rx_cm.clkfbout_mult_frange=(2,65,1);rx_cm.clkout0_divide_range=(2,129,1)
  rx_cm.register_clkin(rxclk,125e6)
  rx_cm.create_clkout(self.cd_eth_rx,125e6,phase=-90)
  self.comb += rx_cm.reset.eq(reset)
  self.submodules.tx=ClockDomainsRenamer('eth_tx')(LiteEthPHYRGMIITX(pads));self.sink=self.tx.sink
  self.source=s=stream.Endpoint(eth_phy_description(8));self.comb += s.be.eq(1)
  rx_data=Signal(8);rx_ctl=Signal(2)
  for pad,lo,hi in [(pads.rx_ctl,rx_ctl[0],rx_ctl[1])]+[(pads.rx_data[i],rx_data[i],rx_data[i+4]) for i in range(4)]:
   raw=Signal()
   self.specials += [Instance('IBUF',i_I=pad,o_O=raw),Instance('IDDRE1',p_DDR_CLK_EDGE='SAME_EDGE_PIPELINED',p_IS_C_INVERTED=0,p_IS_CB_INVERTED=1,
    i_C=self.cd_eth_rx.clk,i_CB=self.cd_eth_rx.clk,i_R=0,i_D=raw,o_Q1=lo,o_Q2=hi)]
  valid_d=Signal()
  self.sync.eth_rx += [valid_d.eq(rx_ctl[0]),s.valid.eq(rx_ctl[0]),s.data.eq(rx_data),
   If(~rx_ctl[0],s.error.eq(0)).Elif(~rx_ctl[1],s.error.eq(1))]
  self.comb += s.last.eq(~rx_ctl[0]&valid_d)
