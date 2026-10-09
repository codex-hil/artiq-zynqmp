"""Wire-level extension of upstream test_link_layer (ARTIQ LGPLv3+).

Unlike upstream's decoded-symbol loopback, traffic crosses actual 8b/10b
encoding, the 20-bit word boundary and decoding. No hardware is simulated.
"""
import unittest
from migen import Module, ClockDomain, ClockDomainsRenamer, Cat
from migen.sim import run_simulation, passive
from artiq.gateware.drtio.link_layer import LinkLayerTX, LinkLayerRX
from raw20_codec import Raw20Codec


class RawLoopback(Module):
    def __init__(self, swap_lanes=False):
        self.clock_domains.cd_rtio_rx = ClockDomain("rtio_rx")
        self.submodules.codec = Raw20Codec()
        self.submodules.tx = LinkLayerTX(self.codec.encoder)
        self.submodules.rx = ClockDomainsRenamer("rtio_rx")(LinkLayerRX(self.codec.decoders))
        wire = Cat(self.codec.tx_raw[10:20], self.codec.tx_raw[0:10]) if swap_lanes else self.codec.tx_raw
        self.comb += self.codec.rx_raw.eq(wire)


class Raw20LinkTests(unittest.TestCase):
    def _packets(self, swap_lanes=False):
        dut = RawLoopback(swap_lanes)

        def scrambler_sync():
            for i in range(32):
                yield

        rt_packets = [
            [0x9970, 0xcdef, 0x0000],
            [0xef00, 0x5678],
            [0xeeee, 0xffff, 0x0304, 0x3344],
            [0x7475, 0x3332, 0x7662, 0x6668, 0x6261]
        ]
        def transmit_rt_packets():
            yield from scrambler_sync()

            for packet in rt_packets:
                yield dut.tx.rt_frame.eq(1)
                for data in packet:
                    yield dut.tx.rt_data.eq(data)
                    yield
                yield dut.tx.rt_frame.eq(0)
                yield
            # flush
            for i in range(20):
                yield

        rx_rt_packets = []
        @passive
        def receive_rt_packets():
            yield from scrambler_sync()

            previous_frame = 0
            while True:
                frame = yield dut.rx.rt_frame
                if frame and not previous_frame:
                    packet = []
                    rx_rt_packets.append(packet)
                previous_frame = frame
                if frame:
                    packet.append((yield dut.rx.rt_data))
                yield

        aux_packets = [
            [0x2, 0x4],
            [0x4, 0x1, 0x8, 0x8],
            [0xb, 0xa, 0xd, 0xc, 0x0, 0xf, 0xe]
        ]
        def transmit_aux_packets():
            yield from scrambler_sync()

            for packet in aux_packets:
                yield dut.tx.aux_frame.eq(1)
                for data in packet:
                    yield dut.tx.aux_data.eq(data)
                    yield
                    while not (yield dut.tx.aux_ack):
                        yield
                yield dut.tx.aux_frame.eq(0)
                yield
                while not (yield dut.tx.aux_ack):
                    yield
            # flush
            for i in range(20):
                yield

        rx_aux_packets = []
        @passive
        def receive_aux_packets():
            yield from scrambler_sync()

            previous_frame = 0
            while True:
                if (yield dut.rx.aux_stb):
                    frame = yield dut.rx.aux_frame
                    if frame and not previous_frame:
                        packet = []
                        rx_aux_packets.append(packet)
                    previous_frame = frame
                    if frame:
                        packet.append((yield dut.rx.aux_data))
                yield

        run_simulation(dut, {"sys": [transmit_rt_packets(), transmit_aux_packets()],
                             "rtio_rx": [receive_rt_packets(), receive_aux_packets()]},
                       clocks={"sys": 8, "rtio_rx": (8, 2)})

        # print("RT:")
        # for packet in rx_rt_packets:
        #     print(" ".join("{:08x}".format(x) for x in packet))
        # print("AUX:")
        # for packet in rx_aux_packets:
        #     print(" ".join("{:02x}".format(x) for x in packet))
        if swap_lanes:
            self.assertNotEqual(rt_packets, rx_rt_packets)
            self.assertNotEqual(aux_packets, rx_aux_packets)
        else:
            self.assertEqual(rt_packets, rx_rt_packets)
            self.assertEqual(aux_packets, rx_aux_packets)

    def test_packets_with_recovered_clock_phase_offset(self):
        self._packets()

    def test_swapped_symbol_lanes_negative_control(self):
        self._packets(swap_lanes=True)

    def test_ready_requires_all_phy_conditions(self):
        dut = Raw20Codec(rx_domain="sys")
        def check():
            for flags in range(16):
                yield dut.rx_reset_done.eq(flags & 1)
                yield dut.rx_clock_active.eq((flags >> 1) & 1)
                yield dut.word_aligned.eq((flags >> 2) & 1)
                yield dut.rx_reset.eq((flags >> 3) & 1)
                yield
                self.assertEqual((yield dut.channel.rx_ready), int(flags == 7))
        run_simulation(dut, check())
