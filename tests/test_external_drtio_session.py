"""Offline acceptance controls for external observation; LGPL-3.0-or-later."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('external_session',
    Path(__file__).resolve().parents[1]/'diagnostics/drtio/external_session.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ExternalObservationTests(unittest.TestCase):
    def exercise(self, status=255, clock_step=62500000, wrap=False):
        with tempfile.TemporaryDirectory() as tmp:
            session = module.ExternalSession.__new__(module.ExternalSession)
            session.output = Path(tmp)
            session.config = {'server':'tcp:localhost:3121'}
            session.result = {}
            session.mapping = {'registers':{}}
            start = 0xffff0000 if wrap else 0
            samples = [[status, (start+i*62500000)&0xffffffff,
                (start+i*clock_step)&0xffffffff, i*62500000, 1,0,0,0,0] for i in range(4)]
            session.run = lambda *a, **kw: '\n'.join('EXTERNAL_SAMPLE '+' '.join(map(str,s))
                for s in samples)+'\nEXTERNAL_OBSERVATION_COMPLETE\n'
            session.observe()
            self.assertEqual(session.result['status'], 'RX_CLOCK_AND_COMMA')
            # No RT/AUX frames required, and no remote discovery claim inferred.
            self.assertIn('not packet/CRC', session.result['scope'])

    def test_idle_remote_and_counter_wrap(self):
        self.exercise()
        self.exercise(wrap=True)

    def test_los_rejects_comma_even_with_running_clocks(self):
        with self.assertRaisesRegex(RuntimeError, 'External RX not confirmed'):
            self.exercise(status=511)

    def test_missing_module_and_wrong_clock_rejected(self):
        with self.assertRaises(RuntimeError): self.exercise(status=127)
        with self.assertRaises(RuntimeError): self.exercise(clock_step=1000)

    def test_restore_failure_is_recorded(self):
        with tempfile.TemporaryDirectory() as tmp:
            session = module.ExternalSession.__new__(module.ExternalSession)
            session.output = Path(tmp)
            session.touched = True
            session.result = {'status':'RX_NOT_CONFIRMED'}
            session.config = {'restore_bitstream':'test.bit','worker':'test','cpu0':'test.elf'}
            session.common = lambda: []
            def fail(*a, **kw): raise RuntimeError('injected loader failure')
            session.run = fail
            with self.assertRaisesRegex(RuntimeError, 'injected loader failure'): session.restore()
            recorded = json.loads((Path(tmp)/'results.json').read_text())
            self.assertEqual(recorded['restoration'], 'FAIL')
            self.assertEqual(recorded['status'], 'RX_NOT_CONFIRMED')
