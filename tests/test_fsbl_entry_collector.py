"""Tcl collector protocol/failure controls, no XSDB/HW; LGPL-3.0-or-later."""
import subprocess
import unittest
from pathlib import Path

LIB = Path(__file__).resolve().parents[1] / 'scripts/collect_fsbl_entry.tcl'
MOCK = '''
set props [dict create name {Cortex-A53 #0} jtag_cable_serial 210383B7F02DA suspended 1]
set regs [dict create pc fffc0bf4 currentel 0000000c sctlr_el3 00000000 daif 000003c0 mpidr_el1 80000000]
set reads {}
proc targets {args} {global props; return [list $props]}
proc rrd {option name} {global regs reads; if {$option ne "-nvlist"} {error option}; lappend reads $name; return [list $name [dict get $regs $name]]}
'''


class CollectorTests(unittest.TestCase):
    def run_tcl(self, body):
        p = subprocess.run(['tclsh'], input=f'source {{{LIB}}}\n'+MOCK+body,
                           capture_output=True, text=True, timeout=5)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertFalse(p.stderr, p.stderr)
        return p.stdout

    def test_hex_and_two_snapshots(self):
        self.assertIn('OK', self.run_tcl('''
set result [fsbl_entry::collect 0xfffc0bf4]
if {[llength $result] != 2 || [dict get [lindex $result 0] currentel] != 12 || [llength $reads] != 10} {error bad}
puts OK
'''))

    def test_rejections(self):
        cases = ['dict set props suspended 0', 'dict set props jtag_cable_serial other',
                 'dict set props name other', 'dict set regs pc fffc0bf0',
                 'dict set regs currentel 4', 'dict set regs sctlr_el3 1005',
                 'dict set regs daif 1c0', 'dict set regs mpidr_el1 80000001',
                 'dict set regs pc malformed']
        for mutation in cases:
            with self.subTest(mutation=mutation):
                self.assertIn('REJECT', self.run_tcl(mutation+'\nif {![catch {fsbl_entry::collect 0xfffc0bf4}]} {error accepted}\nputs REJECT\n'))

    def test_wrong_el_skips_privileged_reads(self):
        self.assertIn('OK',self.run_tcl('''
dict set regs currentel 4
catch {fsbl_entry::collect 0xfffc0bf4}
if {$reads ne {pc currentel}} {error privileged-read}
puts OK
'''))


if __name__ == '__main__': unittest.main()
