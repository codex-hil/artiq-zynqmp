"""Source drift controls for isolated AMD patch; LGPL-3.0-or-later."""
import sys,unittest
from pathlib import Path
REPO=Path(__file__).resolve().parents[1];sys.path.insert(0,str(REPO/'scripts'))
from prepare_spd_vendor import patch
class VendorPatch(unittest.TestCase):
    def test_missing_or_duplicate_anchor_rejected(self):
        for name,anchor in [('xiicps_hw.c','\twhile ((XIicPs_RxDataValid(InstancePtr)) != 0U) {'),('xiicps_master.c','\tXIicPs_MasterIntrRead(InstancePtr, &IntrStatusReg, IsHold);')]:
            for text in ('unrecognized source',anchor+'\n'+anchor):
                with self.subTest(name=name),self.assertRaises(ValueError):patch(name,text)
    def test_second_application_rejected_and_unmodified_xfer_preserved(self):
        anchor='\twhile ((XIicPs_RxDataValid(InstancePtr)) != 0U) {'
        with self.assertRaises(ValueError):patch('xiicps_hw.c',patch('xiicps_hw.c',anchor))
        self.assertEqual(patch('xiicps_xfer.c','unchanged'), 'unchanged')
