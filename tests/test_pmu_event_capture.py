"""Fixed PMUEVENT read and parser controls; LGPL-3.0-or-later."""
import subprocess
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from capture_pmu_events_state import parse
from plan_pmu_events_snapshot import REGISTERS
ROOT = Path(__file__).resolve().parents[1]

class CaptureTests(unittest.TestCase):
    def test_actual_tcl_allowlist(self):
        mock = '''
set argv {server 210383B7F02DA}
set reads {}
proc connect {args} {}
proc disconnect {} {}
proc after {args} {}
proc targets {args} {
 if {[lindex $args 0] eq "-set"} {return}
 return [list [dict create jtag_cable_serial 210383B7F02DA target_id 1]]
}
proc mrd {args} {
 global reads
 if {[lrange $args 0 2] ne {-address-space AP0 -value}} {error unsafe-read}
 lappend reads [lindex $args 3]
 return 0
}
'''
        mock += f'source {{{ROOT / "scripts/probe_pmu_events_state.tcl"}}}\n'
        expected = ' '.join(hex(a) for a in REGISTERS.values())
        mock += f'if {{$reads ne {{{expected} {expected}}}}} {{error wrong-addresses}}\n'
        p = subprocess.run(['tclsh'], input=mock, text=True, capture_output=True, timeout=5)
        self.assertEqual(p.returncode, 0)
        self.assertFalse(p.stderr, p.stderr)
        self.assertTrue(parse(p.stdout)['stable'])
        for bad in [p.stdout + p.stdout, p.stdout.replace('PMUEVENT_END', ''),
                    p.stdout.replace('0xffd40024', '0xffd4002c'),
                    p.stdout.replace('PMUEVENT_BEGIN', 'PMUEVENT 0 gpi1 0xffd40024 0x00000000\nPMUEVENT_BEGIN')]:
            with self.assertRaises(ValueError):
                parse(bad)

if __name__ == '__main__':
    unittest.main()
