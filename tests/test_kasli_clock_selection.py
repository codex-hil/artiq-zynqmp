"""Known-board clock snapshot admission; no hardware. LGPL-3.0-or-later."""
import json,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/'scripts/capture_kasli03_clock.py'
class ClockSelectionTests(unittest.TestCase):
    def test_kasli01_restore_refused_before_hardware_or_output(self):
        with tempfile.TemporaryDirectory() as name:
            p=Path(name);plan=p/'plan.json';plan.write_text(json.dumps({'not_a_qualified_plan':True}))
            out=p/'output'
            r=subprocess.run([sys.executable,str(SCRIPT),'--board','KASLI01','--output',str(out),
                '--si-source',str(SCRIPT),'--restore-plan',str(plan),'--settled-timing'],capture_output=True,text=True)
            self.assertNotEqual(r.returncode,0)
            self.assertIn('KASLI01 restoration is not qualified; snapshot only',r.stderr)
            self.assertFalse(out.exists())
    def test_unknown_board_refused(self):
        r=subprocess.run([sys.executable,str(SCRIPT),'--board','KASLI04'],capture_output=True,text=True)
        self.assertNotEqual(r.returncode,0);self.assertIn('invalid choice',r.stderr)
