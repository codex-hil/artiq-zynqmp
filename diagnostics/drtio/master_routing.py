"""Isolated one-hop master CRI routing; LGPL-3.0-or-later.

Destination0 is local,1 is the sole remote link, all others start unreachable.
Uses upstream owner selection; callers must change ownership only while idle.
No AXI/firmware/DMA/clock-reset integration is implied.
"""
from migen import Module
from artiq.gateware.rtio.cri import CRIInterconnectShared, RoutingTableAccess


class GenesysMasterRouting(Module):
    def __init__(self, initiators, local, remote):
        if not 1 <= len(initiators) <= 2:
            raise ValueError('Initial profile supports one or two explicitly owned initiators')
        self.submodules.fabric = fabric = CRIInterconnectShared(
            initiators, [local, remote], enable_routing=True)
        # Upstream's zero-initialized table would silently send unknown nodes
        # to local I/O. Select its explicit unreachable sink instead.
        fabric.decoder.routing_table.init = [0, 1] + [2] * 254
        self.submodules.routes = RoutingTableAccess(fabric)
        self.owner = fabric.switch.selected

    def get_csrs(self):
        return self.fabric.get_csrs() + self.routes.get_csrs()
