# SPDX-License-Identifier: LGPL-3.0-or-later
"""Construction and unequal-clock transport; no physical CDC qualification."""
import unittest
from migen import ClockDomain, Module
from migen.genlib.resetsync import AsyncResetSynchronizer
from litex.soc.interconnect.axi import AXILiteInterface
from master_ps_cdc import GenesysMasterPSCDC


class Construction(unittest.TestCase):
    def test_five_channels_with_both_reset_synchronizers(self):
        top = Module()
        top.clock_domains.cd_sys = ClockDomain('sys')
        top.clock_domains.cd_master = ClockDomain('master')
        cdc = GenesysMasterPSCDC(AXILiteInterface(), AXILiteInterface())
        top.submodules.cdc = cdc
        self.assertEqual(set(cdc.crossings), {'aw', 'w', 'b', 'ar', 'r'})
        # Every maintained stream crossing must own two common-reset domains.
        for crossing in cdc.crossings.values():
            fragment = crossing.get_fragment()
            self.assertEqual(len(fragment.clock_domains), 2)
            self.assertEqual(sum(isinstance(s, AsyncResetSynchronizer)
                                 for s in fragment.specials), 2)

    def test_invalid_interfaces_refused(self):
        cases = [
            (AXILiteInterface(), AXILiteInterface(), {'master_clock': 'sys'}),
            (AXILiteInterface(data_width=64), AXILiteInterface(), {}),
            (AXILiteInterface(), AXILiteInterface(address_width=40), {}),
            (AXILiteInterface(mode='r'), AXILiteInterface(), {})]
        for ps, master, options in cases:
            with self.subTest(options=options), self.assertRaises(ValueError):
                GenesysMasterPSCDC(ps, master, **options)

class FunctionalReset:
    @staticmethod
    def lower(special):
        m = Module()
        m.comb += special.cd.rst.eq(special.async_reset)
        return m


class Transport(unittest.TestCase):
    def test_unequal_clocks_backpressure(self):
        from migen.sim import run_simulation
        top = Module()
        top.clock_domains.cd_sys = ClockDomain('sys')
        top.clock_domains.cd_master = ClockDomain('master')
        ps, master = AXILiteInterface(address_width=40), AXILiteInterface(address_width=40)
        top.submodules.cdc = cdc = GenesysMasterPSCDC(ps, master)
        clocks = {'sys': 8, 'master': 14}
        for name, crossing in cdc.crossings.items():
            domains = list(crossing._fragment.clock_domains)
            periods = (14, 8) if name in ('b', 'r') else (8, 14)
            for domain, period in zip(domains, periods):
                clocks[domain.name] = period
        completed = []

        def wait(signal):
            for _ in range(160):
                if (yield signal):
                    return
                yield
            self.fail('Bounded channel handshake timed out')

        def send(channel, values):
            for key, value in values.items():
                yield getattr(channel, key).eq(value)
            yield channel.valid.eq(1)
            yield from wait(channel.ready)
            yield
            yield channel.valid.eq(0)

        def receive(channel, values):
            yield from wait(channel.valid)
            # Hold ready low; producer must retain valid and payload.
            for _ in range(7):
                self.assertEqual((yield channel.valid), 1)
                for key, value in values.items():
                    self.assertEqual((yield getattr(channel, key)), value)
                yield
            yield channel.ready.eq(1)
            yield
            yield channel.ready.eq(0)
            yield

        def requester():
            for _ in range(6):
                yield
            for index in range(6):
                yield from send(ps.aw, {'addr': 0xa0000010 + 4*index, 'prot': 0})
                for _ in range(index):
                    yield
                yield from send(ps.w, {'data': 0x12340000+index, 'strb': 15})
                yield from receive(ps.b, {'resp': index % 3})
                yield from send(ps.ar, {'addr': 0xa0000100 + 4*index, 'prot': 0})
                yield from receive(ps.r, {'data': 0xfeed0000+index, 'resp': index % 3})
            completed.append('requester')

        def target():
            for index in range(6):
                yield from receive(master.aw, {'addr': 0xa0000010+4*index, 'prot': 0})
                yield from receive(master.w, {'data': 0x12340000+index, 'strb': 15})
                yield from send(master.b, {'resp': index % 3})
                yield from receive(master.ar, {'addr': 0xa0000100+4*index, 'prot': 0})
                yield from send(master.r, {'data': 0xfeed0000+index, 'resp': index % 3})
            completed.append('target')

        run_simulation(top, {'sys': requester(), 'master': target()}, clocks=clocks,
                       special_overrides={AsyncResetSynchronizer: FunctionalReset})
        self.assertEqual(set(completed), {'requester', 'target'})


if __name__ == '__main__':
    unittest.main()
