"""One-event RTLink mailbox from rio_phy to JESD; latency is asynchronous.

No promise of timestamp-accurate RF. Use a shared clock/timestamp scheduler
for that. Source owns data until acknowledgement; reconnect flushes old
requests before accepting new ones. Runtime source reset must be sampled
by rio_phy; stopped clocks keep the handshake busy.
"""
import env
from migen import *
from migen.genlib.cdc import MultiReg
from rtio_endpoint import EnvelopeRTIO


class EnvelopeRTIOBridge(Module):
    def __init__(self, player, rtlink):
        self.rtlink = rtlink.Interface(rtlink.OInterface(32, enable_replace=False),
                                       rtlink.IInterface(8, timestamped=False))
        self.enable = Signal()
        self.reset = Signal()
        self.ready = Signal()
        self.submodules.endpoint = ep = EnvelopeRTIO(player, rtlink)
        request = Signal(reset_less=True); ack = Signal(reset_less=True)
        self.held = Signal(32, reset_less=True, name='rtio_event_held')
        self.held.attr.add('dont_touch')
        response = Signal(8, reset_less=True, name='rtio_response_held')
        response.attr.add('dont_touch')
        self.result = Signal(8, name='rtio_response_active')
        self.result.attr.add('dont_touch')
        req_j = Signal(); ack_r = Signal(); live_j = Signal(); live_ack_r = Signal()
        live = Signal(reset_less=True); live_ack = Signal()
        reconnect = Signal(reset=1, reset_less=True)
        self.specials += [MultiReg(request, req_j, 'jesd'), MultiReg(ack, ack_r, 'rio_phy'),
                          MultiReg(live, live_j, 'jesd'), MultiReg(live_ack, live_ack_r, 'rio_phy')]
        want = self.enable & ~self.reset & ~ResetSignal('rio_phy')
        busy = request != ack_r
        # Require a complete offline/online round trip on every loss of enable.
        self.sync.rio_phy += If(~want, live.eq(0), reconnect.eq(1)
        ).Elif(reconnect,
            live.eq(0), If(~live_ack_r, live.eq(1), reconnect.eq(0))
        ).Else(live.eq(1))
        pending = Signal(reset_less=True)
        self.comb += [self.ready.eq(want & live & live_ack_r & ~reconnect & ~busy & ~pending),
                      self.rtlink.o.busy.eq(~self.ready)]
        result_capture = Signal(name='rtio_response_capture')
        result_capture.attr.add(('direct_enable', 'yes'));result_capture.attr.add('keep')
        self.comb += [result_capture.eq(pending & ~busy & want & live & live_ack_r & ~reconnect),
                      self.rtlink.i.data.eq(self.result)]
        self.sync.rio_phy += If(result_capture, self.result.eq(response))
        self.sync.rio_phy += [
            self.rtlink.i.stb.eq(0),
            If(self.rtlink.o.stb & self.ready,
                self.held.eq(self.rtlink.o.data), request.eq(~request), pending.eq(1)),
            If(pending & ~busy,
                pending.eq(0),
                If(want & live & live_ack_r & ~reconnect,
                    self.rtlink.i.stb.eq(1))),
            If(~want, pending.eq(0)),
        ]
        # Keep both clocks' protocol tokens across source-only reset. Incoming
        # requests are drained while offline. No old request crosses reconnect.
        idle, capture, execute, reply = range(4)
        state = Signal(2)
        active = Signal(32, name='rtio_event_active')
        active.attr.add('dont_touch')
        capture_enable = Signal(name='rtio_event_capture')
        capture_enable.attr.add(('direct_enable', 'yes'));capture_enable.attr.add('keep')
        self.comb += [capture_enable.eq(live_j & live_ack & (state == capture)),
                      ep.enable.eq(live_j & live_ack), ep.reset.eq(ResetSignal('jesd')),
                      ep.rtlink.o.data.eq(active), ep.rtlink.o.stb.eq((state == execute) & live_j & live_ack)]
        self.sync.jesd += If(capture_enable, active.eq(self.held))
        self.sync.jesd += If(~live_j,
            live_ack.eq(0), ack.eq(req_j), state.eq(idle), response.eq(4)
        ).Elif(~live_ack,
            ack.eq(req_j), state.eq(idle), live_ack.eq(1)
        ).Else(Case(state, {
            idle:If(req_j != ack, state.eq(capture)),
            capture:state.eq(execute),
            execute:state.eq(reply),
            reply:[response.eq(ep.rtlink.i.data), ack.eq(req_j), state.eq(idle)],
        }))
        self.probes = [self.ready, player.armed, player.playing]
        self.overrides = []
