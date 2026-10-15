"""Offline acceptance controls for external observation; LGPL-3.0-or-later."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace
import itertools

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


class ExternalAuxAcceptanceTests(unittest.TestCase):
    def exercise(self, master_ok=True, send_error=False, tsc=False, ack=True, master_tsc_error=False):
        with tempfile.TemporaryDirectory() as tmp:
            session = module.ExternalSession.__new__(module.ExternalSession)
            session.output = Path(tmp)
            session.config = dict(port='fake',server='fake',firmware='fake',artiq_python='fake')
            session.result = {}
            session.tsc_test = tsc
            text = b'AUX_EXTERNAL TX_IDLE_ENABLED destination=DOWN\nAUX_SERVICE RESPOND request=0 reply=1\n'
            if tsc:
                text += b'AUX_TSC BASELINE count=0\n'
                if ack: text += b'AUX_TSC ACK count=1\n'
            if send_error: text += b'AUX_SERVICE SEND_FAIL\n'
            class UART:
                in_waiting = 0
                remaining = text
                def __enter__(self): return self
                def __exit__(self, *args): pass
                def reset_input_buffer(self): pass
                def read(self, size):
                    result=self.remaining;self.remaining=b'';return result
            def run(name, *args, **kwargs):
                if name=='master-tsc-log':
                    return '[LINK#1] link initialization completed'+(' [LINK#1] failed to sync TSC' if master_tsc_error else '')
                return '[LINK#1] remote replied after 1 packets' if master_ok else 'ping failed'
            session.run = run
            with patch.dict('sys.modules',serial=SimpleNamespace(Serial=lambda *a,**kw:UART())):
                with patch.object(module.time,'monotonic',side_effect=itertools.count()):
                    session.observe_aux('fe80::test%eth0')
            self.assertEqual(session.result['status'],'EXTERNAL_TSC_LOAD_ACK' if tsc else 'EXTERNAL_AUX_ECHO')

    def test_both_remote_ends_required(self):
        self.exercise()
        with self.assertRaises(RuntimeError): self.exercise(master_ok=False)

    def test_send_error_rejects_successful_echo(self):
        with self.assertRaises(RuntimeError): self.exercise(send_error=True)

    def test_tsc_requires_actual_ack_and_no_master_timeout(self):
        self.exercise(tsc=True)
        with self.assertRaises(RuntimeError): self.exercise(tsc=True,ack=False)
        with self.assertRaises(RuntimeError): self.exercise(tsc=True,master_tsc_error=True)
