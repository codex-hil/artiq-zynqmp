# SPDX-License-Identifier: LGPL-3.0-or-later
"""PS-export adapter plus native master/raw20/GTH isolated assembly.

Parent provides PS hard-IP instance, actual pins/IP source files and constraints.
No deterministic PHY latency, physical CDC or runtime recovery qualification.
"""
from migen import Module,Signal
from raw20_codec import Raw20Codec
from master_gth_adapter import MasterGTHAdapter
from master_integration import GenesysMasterIntegration

class MasterPhysicalAssembly(Module):
    def __init__(self,ps,pads,refpads):
        request=Signal(reset=1)
        self.submodules.codec=codec=Raw20Codec()
        self.submodules.phy=phy=MasterGTHAdapter(pads,refpads,ps.outputs['pl_clk0'],request,codec.tx_raw)
        self.submodules.core=core=GenesysMasterIntegration(ps,codec.channel,phy.tx_clock,phy.rx_clock,
            codec=codec,link_status=phy.link_status)
        self.comb += [codec.rx_raw.eq(phy.rx_raw),
                      request.eq(core.gt_reset_request | ~ps.outputs['pl_resetn0'])]
        self.sfp_tx_disable=Signal(reset=1)
        self.comb += self.sfp_tx_disable.eq(~core.admit | request)
