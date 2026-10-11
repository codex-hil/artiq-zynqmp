"""Minimal port-local correction to upstream satellite truncation detection.

LGPL-3.0-or-later. Does not modify the pinned or reference ARTIQ checkout.
"""
from migen import FSM
from artiq.gateware.drtio.rt_packet_satellite import RTPacketSatellite

class CheckedRTPacketSatellite(RTPacketSatellite):
    def __init__(self, link_layer, interface=None):
        super().__init__(link_layer, interface)
        candidates = [module for name,module in self._submodules
                      if isinstance(module,FSM) and 'WRITE_CMD' in module.actions]
        if len(candidates) != 1:
            raise ValueError('Upstream satellite RX FSM changed; review truncation overlay')
        actions = candidates[0].actions['INPUT']
        if len(actions) != 1:
            raise ValueError('Upstream satellite INPUT actions changed')
        outer = actions[0]
        truncated = outer.t[-1]
        # Require the exact contradictory nesting: frame & (~frame & ongoing).
        cond = truncated.cond
        if (cond.op != '&' or cond.operands[0].op != '~' or
                cond.operands[0].operands[0] is not outer.cond):
            raise ValueError('Upstream truncation guard changed; review overlay')
        outer.t.pop()
        actions.append(truncated)
