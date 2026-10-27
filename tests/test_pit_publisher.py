"""Publication cut points and ambiguous completion. LGPL-3.0-or-later."""
import struct
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'diagnostics/ddr'))
from pit_publication import accept, OfflinePublisher


class Tests(unittest.TestCase):
    def source(self, nonce=7):
        return struct.pack('<IIQ8I', 1, 1, nonce, *range(8))

    def run_model(self, cut=None, after=False, old=False):
        source = self.source()
        slot = bytearray(self.source(8) if old else bytes(48))
        calls, observations = [], []
        publisher = OfflinePublisher()
        def callback(kind, offset=None, value=None):
            index = len(calls)
            calls.append((kind, offset, value))
            # Nested entry must never reach another callback.
            with self.assertRaises(ValueError):
                publisher.publish(source, 7, write, barrier)
            if index == cut and not after:
                raise OSError('synthetic failure before effect')
            if kind == 'write':
                struct.pack_into('<I', slot, offset, value)
            observations.append(bytes(slot))
            if index == cut and after:
                raise OSError('synthetic failure after effect')
        def write(offset, value): callback('write', offset, value)
        def barrier(): callback('barrier')
        result = publisher.publish(source, 7, write, barrier)
        count = len(calls)
        with self.assertRaises(ValueError): publisher.publish(source, 7, write, barrier)
        self.assertEqual(len(calls), count)
        return result, calls, observations, bytes(slot)

    def test_order_and_acceptance_only_at_commit(self):
        result, calls, snapshots, slot = self.run_model()
        expected = [('write', 0, 0), ('barrier', None, None)]
        words = struct.unpack('<12I', self.source())
        expected += [('write', i * 4, words[i]) for i in range(1, 12)]
        expected += [('barrier', None, None), ('write', 0, 1)]
        self.assertEqual(calls, expected)
        self.assertEqual(result['status'], 'CALLBACKS_RETURNED_OFFLINE')
        for snapshot in snapshots[:-1]:
            with self.assertRaises(ValueError): accept(snapshot, snapshot, 7)
        self.assertFalse(accept(slot, slot, 7)['physical_backend_ready'])

    def test_all_cut_points_before_and_after_effect(self):
        # 15 callbacks x 2 failure modes x fresh/previous-session slot = 60.
        for old in (False, True):
            for after in (False, True):
                for cut in range(15):
                    result, calls, _, slot = self.run_model(cut, after, old)
                    self.assertEqual(result['status'], 'VISIBILITY_UNKNOWN')
                    self.assertEqual(len(calls), cut + 1)
                    self.assertFalse(result['destructive_test_allowed'])
                    if cut == 14 and after:
                        # Commit may be visible despite writer's error: never claim cancellation.
                        accept(slot, slot, 7)
                    else:
                        with self.assertRaises(ValueError): accept(slot, slot, 7)

    def test_buffered_payload_requires_second_barrier(self):
        for omit_payload_barrier in (False, True):
            slot = bytearray(self.source(8))
            pending = []
            barriers = []
            def write(offset, value):
                if offset == 0:
                    struct.pack_into('<I', slot, offset, value)
                else:
                    pending.append((offset, value))
            def barrier():
                barriers.append(1)
                if omit_payload_barrier and len(barriers) == 2:
                    return  # Deliberately broken visibility callback.
                for offset, value in pending:
                    struct.pack_into('<I', slot, offset, value)
                pending.clear()
            result = OfflinePublisher().publish(self.source(), 7, write, barrier)
            self.assertEqual(result['status'], 'CALLBACKS_RETURNED_OFFLINE')
            if omit_payload_barrier:
                with self.assertRaises(ValueError): accept(bytes(slot), bytes(slot), 7)
            else:
                accept(bytes(slot), bytes(slot), 7)

    def test_invalid_source_does_not_call_or_consume(self):
        publisher = OfflinePublisher()
        calls = []
        with self.assertRaises(ValueError):
            publisher.publish(self.source(8), 7, lambda *a: calls.append(a), lambda: None)
        self.assertEqual(calls, [])
        result = publisher.publish(self.source(), 7, lambda *a: calls.append(a), lambda: None)
        self.assertEqual(result['attempted_callbacks'], 15)


if __name__ == '__main__':
    unittest.main()
