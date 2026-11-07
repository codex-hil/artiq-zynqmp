"""Attach upstream AUX SRAM to the SAME native master link; LGPL-3.0-or-later.

Control/CSR/TX logic must share the master clock and reset. Receive-side CDC is
owned by upstream DRTIOAuxController. No PS/GT bridge or reset qualification here.
"""
from migen import Module
from artiq.gateware.drtio.aux_controller import DRTIOAuxController

class GenesysMasterAux(Module):
    def __init__(self,backend,*,control_clock='master',tx_clock='master'):
        # These are caller declarations, not measured clock-domain evidence.
        # A parent must rename backend and attachment together. Different PS/GT
        # clocks need a separately reviewed transaction/CSR CDC boundary.
        if control_clock!=tx_clock:
            raise ValueError('Direct master AUX requires one control/TX clock; add PS CDC first')
        if getattr(backend,'_genesys_aux_owner',False):
            raise ValueError('Native master link already owns an AUX controller')
        if len(backend.link_layer.tx_aux_data)!=4:
            raise ValueError('Expected four AUX bits per two-symbol raw20 cycle')
        backend._genesys_aux_owner=True
        self.link_layer=backend.link_layer
        self.submodules.controller=DRTIOAuxController(self.link_layer)
        self.bus=self.controller.bus
    def get_csrs(self):return self.controller.get_csrs()
