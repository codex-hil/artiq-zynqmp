"""Offline regression checks for observed invalid clock profiles."""
import json
from pathlib import Path
import unittest
from validate_profile import validate

HERE=Path(__file__).resolve().parent
class ProfileTest(unittest.TestCase):
    def setUp(self):
        self.profile=json.loads((HERE/'profile-rx125.json').read_text())
        self.factory=json.loads((HERE/'factory-plan.json').read_text())
    def test_frequency_plan(self):
        result=validate(self.profile,self.factory)
        self.assertEqual(result['vco_hz'],13750000000)
        self.assertEqual(result['output_hz'],156250000)
    def test_integer_mode_rejects_fractional_feedback(self):
        self.profile['writes']['051f']=0x81 # fractional M with integer mode
        with self.assertRaisesRegex(ValueError,'Fractional M divider disabled'):
            validate(self.profile,self.factory)
    def test_hdmi_clock_gates_are_incompatible(self):
        self.profile['writes']['051f']=0x81
        self.profile['writes']['0521']=0x3b
        self.profile['writes']['0b44']=0x2f
        with self.assertRaisesRegex(ValueError,'divider clocks disabled'):
            validate(self.profile,self.factory)
    def test_disabled_detector_cannot_validate_frequency(self):
        self.profile['writes']['0b47']=0xb
        with self.assertRaisesRegex(ValueError,'OOF clock disabled'):
            validate(self.profile,self.factory)
    def test_changed_output_plan_is_rejected(self):
        self.factory['0305']=128
        with self.assertRaisesRegex(ValueError,'Output frequency mismatch'):
            validate(self.profile,self.factory)
if __name__=='__main__':unittest.main()
