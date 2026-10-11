"""Real upstream AUX SRAM across PS/GT clocks and raw20; LGPL-3.0-or-later."""
from migen import Module, Signal, Cat
from aux_endpoint import AuxEndpoint
from test_aux_raw20 import AuxRaw20Test


class AsyncWire(Module):
    def __init__(self, offset):
        self.submodules.endpoint = e = AuxEndpoint()
        self.aux, self.link = e.aux, e.link
        previous = Signal(20)
        self.sync.gth_tx += previous.eq(e.tx_raw)
        wire = Cat(previous, e.tx_raw)
        self.comb += e.rx_raw.eq(wire[offset:offset+20])


class AuxEndpointTest(AuxRaw20Test):
    # Override all inherited cases: no duplicate synchronous tests.
    def test_memory_ring(self):
        self.exercise(0, dut=AsyncWire(0),
                      clocks={'sys':14, 'gth_tx':8, 'rtio_rx':(8,2)},
                      sizes=(1, 3, 17, 256))

    def test_rt_contention_and_alignment(self):
        self.exercise(7, True, dut=AsyncWire(7),
                      clocks={'sys':6, 'gth_tx':8, 'rtio_rx':(8,2)})

    def test_queue_overflow_and_recovery(self):
        self.exercise(3, overflow=True, dut=AsyncWire(3),
                      clocks={'sys':14, 'gth_tx':8, 'rtio_rx':(8,2)})

# Do not rediscover the imported synchronous base class here.
del AuxRaw20Test
