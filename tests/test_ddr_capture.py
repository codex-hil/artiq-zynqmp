"""Read-only capture admission, no hardware; LGPL-3.0-or-later."""
import sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import capture_ddr_config as capture


class Capture(unittest.TestCase):
    def test_default_is_offline(self):
        with tempfile.TemporaryDirectory() as d,patch.object(sys,'argv',['capture','--output',str(Path(d)/'out')]),patch.object(capture,'lease') as lease,patch.object(capture,'bounded') as bounded:
            self.assertEqual(capture.main(),0);lease.assert_not_called();bounded.assert_not_called()

    def test_busy_lease_does_not_start_transport(self):
        with tempfile.TemporaryDirectory() as d,patch.object(sys,'argv',['capture','--execute','--server','fixture','--output',str(Path(d)/'out')]),patch.object(capture,'lease',side_effect=RuntimeError('BUSY')),patch.object(capture,'bounded') as bounded:
            with self.assertRaisesRegex(RuntimeError,'BUSY'):capture.main()
            bounded.assert_not_called()

if __name__=='__main__':unittest.main()
