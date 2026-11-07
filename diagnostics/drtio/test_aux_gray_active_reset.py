# SPDX-License-Identifier: LGPL-3.0-or-later
"""Active native-format RX abort; coordinated reset and retained SRAM model."""
import unittest
from migen import Module, Signal, ClockDomain
from migen.sim import Simulator
from migen.fhdl.simplify import MemoryToArray
from aux_receiver_gray import GrayBoundedReceiver


class ActiveResetTests(unittest.TestCase):
    def test_partial_packet_abort_and_fresh_recovery(self):
        for words in (1, 7, 255):
            with self.subTest(partial_words=words):
                self.exercise(words)

    def exercise(self, count):
        d=Module()
        d.clock_domains.cd_sys=ClockDomain('sys')
        d.clock_domains.cd_rtio_rx=ClockDomain('rtio_rx')
        class Link:
            rx_aux_data=Signal(4)
            rx_aux_stb=Signal()
            rx_aux_frame=Signal()
        link=Link()
        d.submodules.receiver=r=GrayBoundedReceiver(link,32)
        port=r.mem.get_port(async_read=True)
        d.specials+=port
        def payload(words):
            yield link.rx_aux_frame.eq(1)
            yield link.rx_aux_stb.eq(1)
            for word in words:
                for nibble in range(8):
                    yield link.rx_aux_data.eq((word>>(4*nibble))&15)
                    yield
        def test():
            yield from payload([0x11110000+i for i in range(count)])
            # Drain registered final nibble; one extra partial symbol is harmless.
            yield
            # Keep frame asserted but pause valid symbols: no EOP delivered.
            yield link.rx_aux_stb.eq(0)
            for _ in range(12):yield
            self.assertEqual((yield r.aux_rx_present.w),0)
            self.assertEqual((yield r.write_position.binary),0)
            yield port.adr.eq(0)
            yield
            self.assertEqual((yield port.dat_r),0x11110000)
            yield d.cd_sys.rst.eq(1)
            yield d.cd_rtio_rx.rst.eq(1)
            yield link.rx_aux_frame.eq(0)
            for _ in range(24):yield
            yield d.cd_sys.rst.eq(0)
            yield d.cd_rtio_rx.rst.eq(0)
            for _ in range(24):
                self.assertEqual((yield r.aux_rx_present.w),0)
                yield
            self.assertEqual((yield port.dat_r),0x11110000)
            self.assertEqual((yield r.aux_rx_error.w),0)
            self.assertEqual((yield r.read_position.binary),0)
            # Admission restarts with a new frame, never the old fragment tail.
            yield from payload([0xabcdef01,0x76543210])
            yield link.rx_aux_frame.eq(0)
            yield
            yield link.rx_aux_stb.eq(0)
            for _ in range(30):yield
            self.assertEqual((yield r.aux_rx_present.w),1)
            self.assertEqual((yield r.write_position.binary),1)
            self.assertEqual((yield r.aux_read_pointer.w),0)
            self.assertEqual((yield r.aux_rx_error.w),0)
            for offset,word in enumerate((0xabcdef01,0x76543210)):
                yield port.adr.eq(offset)
                yield
                self.assertEqual((yield port.dat_r),word)
        fragment=d.get_fragment()
        memory_model=MemoryToArray()
        memory_model.transform_fragment(None,fragment)
        for word in memory_model.replacements[r.mem]:word.reset_less=True
        with Simulator(fragment,{'rtio_rx':test()},clocks={'rtio_rx':8,'sys':(22,3)}) as sim:
            sim.run()

if __name__=='__main__':unittest.main()
