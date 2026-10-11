"""Checked LiteX AXI-Lite error propagation overlay; LGPL-3.0-or-later."""
from migen import Signal, Mux, NextValue
from migen.fhdl.structure import If, _Assign
from litex.soc.interconnect.axi import AXILite2Wishbone


class CheckedAXILite2Wishbone(AXILite2Wishbone):
    """Reuse upstream FSM; latch Wishbone ERR as AXI SLVERR.

    The pinned upstream implementation waits only for ACK and always replies
    OKAY. This local overlay supports only its non-low-latency mode, retaining
    upstream arbitration, byte strobes and address subtraction.
    """
    def __init__(self, axi_lite, wishbone, base_address=0):
        super().__init__(axi_lite, wishbone, base_address=base_address,
                         low_latency=False)
        response = Signal(2)
        for name in ('DO-READ', 'DO-WRITE'):
            terminal = self.fsm.actions[name][-1]
            if not isinstance(terminal, If) or terminal.cond is not wishbone.ack:
                raise ValueError('Unsupported LiteX Wishbone completion FSM')
            terminal.cond = wishbone.ack | wishbone.err
            terminal.t.insert(0, NextValue(response, Mux(wishbone.err, 2, 0)))
        count = 0
        for name, port in (('SEND-READ-RESPONSE',axi_lite.r),
                           ('SEND-WRITE-RESPONSE',axi_lite.b)):
            for statement in self.fsm.actions[name]:
                if isinstance(statement, _Assign) and statement.l is port.resp:
                    statement.r = response
                    count += 1
        if count != 2:
            raise ValueError('Unsupported LiteX AXI response FSM')

