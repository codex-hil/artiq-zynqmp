"""No fault waiver for remaining clock path. LGPL-3.0-or-later."""
import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'diagnostics/kasli-master'))
from removed_eem_mux import apply

class OverlayTests(unittest.TestCase):
    def test_only_eem_selection_removed(self):
        source='        i2c::switch_select(BUSNO, 0x70, 0)?;\n        i2c::switch_select(BUSNO, 0x71, 1 << 3)?;\nif ident()? != 0x0182 { return Err("identity"); }\n'
        result=apply(source)
        self.assertNotIn('switch_select(BUSNO, 0x70',result)
        self.assertTrue(result.endswith(source.split('\n',1)[1]))
        with self.assertRaises(ValueError):apply(result)
        with self.assertRaises(ValueError):apply(source+source)
