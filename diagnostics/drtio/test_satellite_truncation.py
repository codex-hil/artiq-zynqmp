"""Regression and negative control for truncated satellite packet headers.

LGPL-3.0-or-later. Original checkouts remain unchanged.
"""
import unittest
from types import SimpleNamespace
from migen import Module, Signal
from migen.sim import run_simulation
from artiq.gateware.drtio.rt_packet_satellite import RTPacketSatellite
from satellite_packet import CheckedRTPacketSatellite

def packet_interface():
    return SimpleNamespace(tx_rt_frame=Signal(), tx_rt_data=Signal(16),
                           rx_rt_frame=Signal(), rx_rt_data=Signal(16))

class TruncationTest(unittest.TestCase):
    def exercise(self, engine, expected):
        dut=Module()
        link=packet_interface()
        dut.submodules.satellite=engine(link)
        pulses=[]
        def run():
            for _ in range(4):yield
            yield link.rx_rt_data.eq(2)  # write header requires multiple words
            yield link.rx_rt_frame.eq(1)
            yield
            yield link.rx_rt_frame.eq(0)
            for _ in range(12):
                pulses.append((yield dut.satellite.packet_truncated))
                self.assertEqual((yield dut.satellite.cri.cmd),0)
                yield
        run_simulation(dut,run())
        self.assertEqual(sum(pulses),expected)
    def test_original_negative_control(self):self.exercise(RTPacketSatellite,0)
    def test_corrected_reports_once(self):self.exercise(CheckedRTPacketSatellite,1)

    def test_complete_unknown_type_reports_once(self):
        dut=Module()
        link=packet_interface()
        dut.submodules.satellite=CheckedRTPacketSatellite(link)
        unknown=[]
        truncated=[]
        def run():
            for _ in range(4):yield
            yield link.rx_rt_data.eq(0xff)
            yield link.rx_rt_frame.eq(1)
            # Unknown Array index clamps to final layout (six-word read).
            for _ in range(6):
                unknown.append((yield dut.satellite.unknown_packet_type))
                truncated.append((yield dut.satellite.packet_truncated))
                yield
            yield link.rx_rt_frame.eq(0)
            for _ in range(12):
                unknown.append((yield dut.satellite.unknown_packet_type))
                truncated.append((yield dut.satellite.packet_truncated))
                self.assertEqual((yield dut.satellite.cri.cmd),0)
                yield
        run_simulation(dut,run())
        self.assertEqual(sum(unknown),1)
        self.assertEqual(sum(truncated),0)
