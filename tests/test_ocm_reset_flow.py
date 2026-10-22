"""OCM loader reset ordering model; LGPL-3.0-or-later."""
import subprocess,tempfile,unittest
from pathlib import Path
REPO=Path(__file__).resolve().parents[1]

class ResetFlow(unittest.TestCase):
    def run_flow(self,fail=False):
        with tempfile.TemporaryDirectory() as d:
            ps=Path(d)/'ps.tcl'
            ps.write_text('\n'.join('set '+name+' {}' for name in ('psu_mio_init_data','psu_peripherals_pre_init_data','psu_pll_init_data','psu_clock_init_data','psu_peripherals_init_data','psu_resetin_init_data','psu_resetout_init_data')))
            model='''
set selected 0
proc connect {args} {}
proc disconnect {} {}
proc configparams {name value} {
 if {$name ne "source-line-view" || $value != 0} {error "Unexpected debugger configuration"}
 puts SOURCE_VIEW_DISABLED
}
proc after {args} {}
proc targets {args} {
 global selected
 if {[lindex $args 0] eq "-set"} {set selected [lindex $args 1];return}
 if {[lindex $args end] eq "is_current == 1"} {return [list [dict create suspended 1]]}
 return [list [dict create target_id 1 jtag_cable_serial 210383B7F02DA]]
}
proc mwr {address value} {
 if {$address ne "0xFF5E0200" || $value ne "0x10E"} {error "Unexpected write"}
 puts ALT_JTAG
}
proc rst {args} {
 global fail
 puts "RESET $args"
 if {$fail && [lindex $args 0] eq "-system"} {error "Reset failed"}
}
proc init_ps {args} {puts INIT_PS}
proc init_peripheral {} {puts INIT_PERIPHERAL}
proc dow {args} {puts DOWNLOAD}
proc con {} {puts CONTINUE}
proc stop {} {error "Already suspended: must not call stop"}
'''
            text=f'set fail {int(fail)}\n'+model+f'\nset argv [list fixture image {{{ps}}} 210383B7F02DA]\nif {{[catch {{source {{{REPO}/scripts/run_ocm_environment.tcl}}}} message]}} {{puts stderr $message;exit 1}}\n'
            return subprocess.run(['tclsh'],input=text,capture_output=True,text=True,timeout=3)
    def test_reset_before_setup_download_without_cache_bypass(self):
        r=self.run_flow();self.assertEqual(r.returncode,0,r.stderr)
        markers=['SOURCE_VIEW_DISABLED','ALT_JTAG','RESET -system','INIT_PS','INIT_PERIPHERAL','RESET -processor -clear-registers','DOWNLOAD','CONTINUE']
        offsets=[r.stdout.index(m) for m in markers];self.assertEqual(offsets,sorted(offsets))
        source=(REPO/'scripts/run_ocm_environment.tcl').read_text();self.assertNotIn('bypass-cache-sync',source);self.assertNotIn('psu_ddr_init_data',source)
    def test_failed_system_reset_prevents_init_and_download(self):
        r=self.run_flow(True);self.assertNotEqual(r.returncode,0)
        self.assertNotIn('INIT_PS',r.stdout);self.assertNotIn('DOWNLOAD',r.stdout)
