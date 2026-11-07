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


class StoppedClock(unittest.TestCase):
    def test_queued_write_reset_and_restart(self):
        from migen.sim import Simulator
        top = Module()
        top.clock_domains.cd_sys = ClockDomain('sys')
        top.clock_domains.cd_master = ClockDomain('master')
        ps, master = AXILiteInterface(), AXILiteInterface()
        top.submodules.cdc = cdc = GenesysMasterPSCDC(ps, master)
        clocks = {'sys': 8, 'master': 14}
        stopped_domains = {'master'}
        for name, crossing in cdc.crossings.items():
            domains = list(crossing._fragment.clock_domains)
            periods = (14, 8) if name in ('b', 'r') else (8, 14)
            for domain, period in zip(domains, periods):
                clocks[domain.name] = period
                if period == 14:
                    stopped_domains.add(domain.name)
        state = {'stop': True, 'suppressed_rising': 0, 'delivered_rising': 0}

        def test():
            yield master.aw.ready.eq(1)
            yield master.w.ready.eq(1)
            yield ps.aw.addr.eq(0xa0000010)
            yield ps.aw.valid.eq(1)
            yield ps.w.data.eq(0x12345678)
            yield ps.w.strb.eq(15)
            yield ps.w.valid.eq(1)
            # Both independent FIFO inputs must accept without destination edges.
            for _ in range(40):
                if (yield ps.aw.ready) and (yield ps.w.ready):
                    break
                yield
            else:
                self.fail('FIFO inputs not ready')
            yield
            yield ps.aw.valid.eq(0)
            yield ps.w.valid.eq(0)
            for _ in range(24):
                self.assertEqual((yield master.aw.valid), 0)
                self.assertEqual((yield master.w.valid), 0)
                self.assertEqual((yield ps.b.valid), 0)
                yield
            self.assertEqual(state['delivered_rising'], 0)
            self.assertGreater(state['suppressed_rising'], 0)
            # Requester abandons this transaction. Reset target and both domains.
            yield top.cd_sys.rst.eq(1)
            yield top.cd_master.rst.eq(1)
            for _ in range(12):
                yield
            # Functional simulator reset executes on edges: retain reset through
            # restart. This does NOT qualify asynchronous reset while stopped.
            state['stop'] = False
            for _ in range(16):
                yield
            yield top.cd_sys.rst.eq(0)
            yield top.cd_master.rst.eq(0)
            for _ in range(24):
                self.assertEqual((yield master.aw.valid), 0)
                self.assertEqual((yield master.w.valid), 0)
                self.assertEqual((yield ps.b.valid), 0)
                yield
            # A fresh write crosses after reset; payload must not be old request.
            yield master.aw.ready.eq(0)
            yield master.w.ready.eq(0)
            yield ps.aw.addr.eq(0xa0000020)
            yield ps.w.data.eq(0xcafef00d)
            yield ps.aw.valid.eq(1)
            yield ps.w.valid.eq(1)
            yield
            yield ps.aw.valid.eq(0)
            yield ps.w.valid.eq(0)
            for _ in range(80):
                if (yield master.aw.valid) and (yield master.w.valid):
                    break
                yield
            else:
                self.fail('Fresh request did not cross after restart')
            self.assertEqual((yield master.aw.addr), 0xa0000020)
            self.assertEqual((yield master.w.data), 0xcafef00d)
            self.assertGreater(state['delivered_rising'], 0)

        with Simulator(top, test(), clocks=clocks,
                       special_overrides={AsyncResetSynchronizer: FunctionalReset}) as sim:
            original_tick = sim.time.tick
            def tick():
                dt, rising, falling = original_tick()
                affected = rising & stopped_domains
                if state['stop']:
                    state['suppressed_rising'] += len(affected)
                    rising -= stopped_domains
                    falling -= stopped_domains
                else:
                    state['delivered_rising'] += len(affected)
                return dt, rising, falling
            sim.time.tick = tick
            sim.run()


class CommittedWrite(unittest.TestCase):
    def test_reset_discards_response_without_undo_or_retry(self):
        from migen.sim import run_simulation, passive
        top = Module()
        top.clock_domains.cd_sys = ClockDomain('sys')
        top.clock_domains.cd_master = ClockDomain('master')
        ps, master = AXILiteInterface(), AXILiteInterface()
        top.submodules.cdc = cdc = GenesysMasterPSCDC(ps, master)
        clocks = {'sys': 8, 'master': 14}
        for name, crossing in cdc.crossings.items():
            periods = (14, 8) if name in ('b', 'r') else (8, 14)
            for domain, period in zip(crossing._fragment.clock_domains, periods):
                clocks[domain.name] = period
        commits = []  # External side effects intentionally survive bus reset.

        @passive
        def target():
            aw = data = None
            response = False
            yield master.aw.ready.eq(1)
            yield master.w.ready.eq(1)
            while True:
                if (yield top.cd_master.rst):
                    aw = data = None
                    response = False
                else:
                    if (yield master.aw.valid) and (yield master.aw.ready):
                        aw = (yield master.aw.addr)
                    if (yield master.w.valid) and (yield master.w.ready):
                        data = (yield master.w.data)
                    if response and (yield master.b.ready):
                        response = False
                    if aw is not None and data is not None:
                        commits.append((aw, data))
                        aw = data = None
                        response = True
                yield master.b.valid.eq(response)
                yield master.b.resp.eq(0)
                yield

        def wait(signal):
            for _ in range(160):
                if (yield signal):
                    return
                yield
            self.fail('Bounded handshake timed out')

        def send(channel, field, value):
            yield getattr(channel, field).eq(value)
            yield channel.valid.eq(1)
            yield from wait(channel.ready)
            yield
            yield channel.valid.eq(0)

        def requester():
            yield ps.w.strb.eq(15)
            yield from send(ps.aw, 'addr', 0xa0000010)
            yield from send(ps.w, 'data', 0x12345678)
            yield from wait(ps.b.valid)
            self.assertEqual(commits, [(0xa0000010, 0x12345678)])
            # PS has not accepted B: a real side effect exists without completion.
            self.assertEqual((yield ps.b.ready), 0)
            yield top.cd_sys.rst.eq(1)
            yield top.cd_master.rst.eq(1)
            for _ in range(16):
                yield
            yield top.cd_sys.rst.eq(0)
            yield top.cd_master.rst.eq(0)
            for _ in range(30):
                self.assertEqual((yield ps.b.valid), 0)
                self.assertEqual((yield master.aw.valid), 0)
                self.assertEqual((yield master.w.valid), 0)
                self.assertEqual(len(commits), 1)
                yield
            yield from send(ps.aw, 'addr', 0xa0000020)
            yield from send(ps.w, 'data', 0xcafef00d)
            yield from wait(ps.b.valid)
            self.assertEqual((yield ps.b.resp), 0)
            yield ps.b.ready.eq(1)
            yield
            yield ps.b.ready.eq(0)
            for _ in range(16):
                yield
            self.assertEqual(commits, [(0xa0000010, 0x12345678),
                                       (0xa0000020, 0xcafef00d)])
            self.assertEqual((yield ps.b.valid), 0)

        run_simulation(top, {'sys': requester(), 'master': target()}, clocks=clocks,
                       special_overrides={AsyncResetSynchronizer: FunctionalReset})


if __name__ == '__main__':
    unittest.main()
