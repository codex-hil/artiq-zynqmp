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
            self.assertIn('KASLI01 restoration requires explicit matching baseline',r.stderr)
            self.assertFalse(out.exists())
    def test_unknown_board_refused(self):
        r=subprocess.run([sys.executable,str(SCRIPT),'--board','KASLI04'],capture_output=True,text=True)
        self.assertNotEqual(r.returncode,0);self.assertIn('invalid choice',r.stderr)

    def test_actual_board_baseline_and_wrong_board_plan_refused(self):
        import copy
        sys.path.insert(0,str(ROOT/'scripts'))
        from kasli_clock_binding import validate
        baseline=ROOT/'evidence/kasli01-identification-clock-2026-10-20/clock-snapshot.json'
        planfile=Path('/srv/codex-hil-data/artiq-zynqmp/build/kasli01-clock-restore-plan-2026-10-20.json')
        sourcefile=Path('/srv/codex-hil-data/artiq-zynqmp/reference/artiq/artiq/firmware/libboard_artiq/si5324.rs')
        if not planfile.exists():self.skipTest('Prepared clock plan absent')
        plan=json.loads(planfile.read_text());source=sourcefile.read_text()
        self.assertEqual(validate('KASLI01',plan,baseline,source)['board'],'KASLI01')
        with self.assertRaises(ValueError):validate('KASLI03',plan,baseline,source)
        bad=copy.deepcopy(plan);bad['configuration_to_compare_then_restore'][0]['value']^=1
        with self.assertRaises(ValueError):validate('KASLI01',bad,baseline,source)

    def test_kasli04_plan_binds_actual_baseline(self):
        import copy
        sys.path.insert(0,str(ROOT/'scripts'))
        from kasli_clock_binding import validate
        baseline=ROOT/'evidence/kasli04-clock-cpu-2026-10-21/results.json'
        planfile=ROOT/'evidence/kasli04-clock-plan-2026-10-21/plan.json'
        sourcefile=Path('/srv/codex-hil-data/artiq-zynqmp/reference/artiq/artiq/firmware/libboard_artiq/si5324.rs')
        if not sourcefile.exists():self.skipTest('Pinned driver source absent')
        plan=json.loads(planfile.read_text());source=sourcefile.read_text()
        self.assertEqual(validate('KASLI04',plan,baseline,source)['dna'],'0x006c440674704854')
        self.assertEqual(plan['mux_addresses'],[0x71])
        self.assertEqual(plan['runtime_locks'],['genesys-210383B7F02DA','kasli-KASLI04'])
        with self.assertRaises(ValueError):validate('KASLI01',plan,baseline,source)
        bad=copy.deepcopy(plan);bad['configuration_to_compare_then_restore'][0]['value']^=1
        with self.assertRaises(ValueError):validate('KASLI04',bad,baseline,source)
