# SPDX-License-Identifier: LGPL-3.0-or-later
import unittest
from migen import Module, Signal
from migen.sim import run_simulation
from aux_controller_gray import GrayAuxController


class ControllerTests(unittest.TestCase):
    def test_wishbone_csr_layout_and_rx_wrap(self):
        d = Module()
        class Link:
            tx_aux_data = Signal(4)
            tx_aux_frame = Signal()
            tx_aux_ack = Signal()
            rx_aux_data = Signal(4)
            rx_aux_stb = Signal()
            rx_aux_frame = Signal()
        link = Link()
        d.submodules.aux = aux = GrayAuxController(link)
        self.assertEqual([c.name for c in aux.get_csrs()],
                         ['aux_tx_length', 'aux_tx', 'aux_rx_present',
                          'aux_rx_error', 'aux_read_pointer'])
        packets = [[(i+1)*0x01020304 ^ j for j in range((1, 3, 17)[i % 3])]
                   for i in range(12)]
        state = {'consumed': 0}
        def producer():
            for index, packet in enumerate(packets):
                for _ in range(3000):
                    if state['consumed'] == index:
                        break
                    yield
                else:
                    self.fail('Wishbone consumer timeout')
                yield link.rx_aux_stb.eq(1)
                yield link.rx_aux_frame.eq(1)
                for word in packet:
                    for nibble in range(8):
                        yield link.rx_aux_data.eq((word >> (4*nibble)) & 15)
                        yield
                yield link.rx_aux_frame.eq(0)
                yield
                yield link.rx_aux_stb.eq(0)
                for _ in range(10):
                    yield
        def consumer():
            # Native TX SRAM window remains writable independently of RX.
            yield from aux.bus.write(0, 0xfeedcafe)
            self.assertEqual((yield from aux.bus.read(0)), 0xfeedcafe)
            for index, packet in enumerate(packets):
                for _ in range(3000):
                    if (yield from aux.receiver.aux_rx_present.read()):
                        break
                    yield
                else:
                    self.fail('RX CSR did not publish')
                slot = yield from aux.receiver.aux_read_pointer.read()
                self.assertEqual(slot, index % 8)
                actual = []
                for offset in range(len(packet)):
                    actual.append((yield from aux.bus.read(8192//4+slot*256+offset)))
                self.assertEqual(actual, packet)
                self.assertEqual((yield from aux.receiver.aux_rx_error.read()), 0)
                # RX window must remain read-only.
                yield from aux.bus.write(8192//4+slot*256, 0xdeadbeef)
                self.assertEqual((yield from aux.bus.read(8192//4+slot*256)), packet[0])
                yield from aux.receiver.aux_rx_present.write(1)
                for _ in range(10):
                    yield
                state['consumed'] += 1
            self.assertEqual((yield from aux.receiver.aux_rx_present.read()), 0)
            self.assertEqual((yield from aux.bus.read(0)), 0xfeedcafe)
        run_simulation(d, {'rtio_rx': producer(), 'sys': consumer()},
                       clocks={'rtio_rx': 8, 'sys': (22, 3)})
        self.assertEqual(state['consumed'], 12)

if __name__ == '__main__':
    unittest.main()
