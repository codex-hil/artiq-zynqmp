"""ARTIQ RTLink endpoint in the JESD clock domain; see RTIO_INTERFACE.rst.

The caller supplies its upstream artiq.gateware.rtio.rtlink module. This
avoids importing/initializing a second ARTIQ version in a satellite target.
"""
import env
from migen import *

QUERY, FIRE, CANCEL = 0, 1, 2
ACCEPTED, BAD_COMMAND, NOT_ARMED, STALE_ARM, DISABLED = range(5)


def start_word(arm_id):
    if isinstance(arm_id, bool) or not isinstance(arm_id, int) or not 0 <= arm_id < 2**30:
        raise ValueError('ARM ID must be a30-bit integer')
    return (arm_id << 2) | FIRE


class EnvelopeRTIO(Module):
    """Synchronous endpoint: rio_phy and JESD must be the SAME clock domain.

    Input response is NOT timestamped and acknowledges command admission,
    not pulse completion. O.busy is always0: rejected commands are consumed
    and explicitly reported, never queued for a later ARM.
    """
    def __init__(self, player, rtlink):
        self.rtlink = rtlink.Interface(rtlink.OInterface(32, enable_replace=False),
                                       rtlink.IInterface(8, timestamped=False))
        self.enable = Signal()  # high only while the timeline/reset is valid
        self.reset = Signal()
        o, i = self.rtlink.o, self.rtlink.i
        command = o.data[:2]; tag = o.data[2:]
        code = Signal(4)
        allowed = self.enable & ~self.reset
        self.comb += [
            o.busy.eq(0), code.eq(ACCEPTED),
            If(~allowed, code.eq(DISABLED)
            ).Elif(command == FIRE,
                If(~player.trigger_ready, code.eq(NOT_ARMED)
                ).Elif(tag != player.arm_id, code.eq(STALE_ARM))
            ).Elif(command == 3, code.eq(BAD_COMMAND)),
            player.trigger.eq(o.stb & (command == FIRE) & (code == ACCEPTED)),
            player.cancel.eq(~allowed | (o.stb & (command == CANCEL))),
        ]
        self.sync.jesd += [i.stb.eq(o.stb),
                          If(o.stb, i.data.eq(Cat(code, player.armed, player.playing, Constant(0, 2))))]
        self.probes = [player.armed, player.playing]
        self.overrides = []
