# SPDX-License-Identifier: LGPL-3.0-or-later
"""Isolated integration assembly using a caller-provided exported PS adapter.

No PS primitive, GTH wizard, pin constraints, firmware, DMA engine or board
configuration is instantiated. Parent supplies actual PS IP adapter, encoded
channel and master TX/RX clocks. Clock/timing/reset physical gates remain open.
"""
from migen import Module,ClockDomain,Signal
from migen.genlib.resetsync import AsyncResetSynchronizer
from artiq.gateware import rtio
from artiq.gateware.rtio.phy import ttl_simple
from artiq.gateware.drtio.core import SyncRTIO
from master_backend import GenesysMasterBackend
from master_routing import GenesysMasterRouting
from master_aux import GenesysMasterAux
from aux_controller_gray import GrayAuxController
from master_csr import GenesysMasterCSR
from master_dual_ingress import MasterDualIngress
from ps_management_hpm import connect_target_hpm0,connect_management_hpm1

class GenesysMasterIntegration(Module):
    def __init__(self,ps,channel,tx_clock,rx_clock,*,codec=None,link_status=None):
        if (codec is None)!=(link_status is None):
            raise ValueError('Codec and physical status must be supplied together')
        if codec is not None and codec.channel is not channel:
            raise ValueError('Link boundary must own the same encoded channel')
        for name in ('management','control','ps','sys','rtio_rx','rio','rio_phy'):
            setattr(self.clock_domains,'cd_'+name,ClockDomain(name))
        pl_clock=ps.outputs['pl_clk0']
        for name in ('management','control','ps'):
            self.comb+=getattr(self,'cd_'+name).clk.eq(pl_clock)
        for name in ('sys','rio','rio_phy'):
            self.comb+=getattr(self,'cd_'+name).clk.eq(tx_clock)
        self.comb+=self.cd_rtio_rx.clk.eq(rx_clock)
        for name in ('management','control'):
            self.specials+=AsyncResetSynchronizer(getattr(self,'cd_'+name),~ps.outputs['pl_resetn0'])
        self.submodules.time=rtio.TSC(glbl_fine_ts_width=3)
        self.submodules.kernel=rtio.KernelInitiator(self.time,now64=True)
        self.submodules.master=GenesysMasterBackend(self.time,channel)
        self.local_outputs=[Signal(),Signal()]
        self.submodules.phy0=p0=ttl_simple.Output(self.local_outputs[0])
        self.submodules.phy1=p1=ttl_simple.Output(self.local_outputs[1])
        self.submodules.local=SyncRTIO(self.time,[rtio.Channel.from_phy(p0),rtio.Channel.from_phy(p1)],lane_count=4,fifo_depth=8)
        self.submodules.routing=GenesysMasterRouting([self.kernel.cri],self.local.cri,self.master.cri)
        self.submodules.aux=GenesysMasterAux(self.master,controller_type=GrayAuxController)
        self.submodules.csr=GenesysMasterCSR(self.time,self.kernel,self.master,self.routing,aux=self.aux,ps_clock='ps')
        self.submodules.ingress=g=MasterDualIngress(self.csr.axi)
        for index,name in enumerate(('ps','sys','rtio_rx','rio','rio_phy')):
            self.comb+=getattr(self,'cd_'+name).rst.eq(g.reset_out[index] | ~ps.outputs['pl_resetn0'])
        connect_target_hpm0(self,ps,g.target_axi,pl_clock)
        connect_management_hpm1(self,ps,g.management_axi,pl_clock)
        self.admit=g.admit
        self.gt_reset_request=g.coordinator.reset
        if codec is not None:
            from master_link_boundary import MasterLinkBoundary
            self.submodules.link_boundary=MasterLinkBoundary(codec,g.admit,
                g.coordinator.reset,link_status)
        # Parent must gate incoming packet admission/reset actual transceiver;
        # this output alone does not synchronize admission into recovered RX.
