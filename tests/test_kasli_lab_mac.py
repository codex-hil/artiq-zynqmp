"""Volatile per-board network overlay checks, no hardware. LGPL-3.0-or-later."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'diagnostics/kasli-master'))
from lab_mac import literal,apply,DEFAULT
class MACTests(unittest.TestCase):
    def test_one_network_identity_shared_by_bootloader_and_runtime(self):
        source='let hardware_addr = '+literal(DEFAULT)+';'
        changed=apply(source,'02:4b:01:48:48:54')
        self.assertNotEqual(source,changed)
        self.assertIn('0x01',changed)
        with self.assertRaises(ValueError):apply(source+source,'02:4b:01:48:48:54')
    def test_multicast_global_or_malformed_refused(self):
        for mac in ['03:4b:01:48:48:54','00:4b:01:48:48:54','02:01','bad']:
            with self.assertRaises(ValueError):literal(mac)
