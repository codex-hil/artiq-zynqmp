"""Tcl DAP observer controls with explicit memory model; LGPL-3.0-or-later."""
import subprocess,tempfile,unittest
from pathlib import Path
REPO=Path(__file__).resolve().parents[1]


class FailstopProbe(unittest.TestCase):
    def run_probe(self,scenario):
        message=b'RPC reply command invalid'
        words={0x200ff004:5,0x200ff040:10,0x200ff044:7,0x200ff048:len(message)}
        for i in range(0,len(message),4):words[0x200ff100+i]=int.from_bytes(message[i:i+4].ljust(4,b'\0'),'little')
        if scenario=='wrong_command':words[0x200ff004]=4
        if scenario=='no_event':words[0x200ff044]=6
        if scenario=='wrong_message':words[0x200ff100]^=1
        text='set memory [dict create '+ ' '.join(f'{k} {v}' for k,v in words.items())+']\n'
        text+='''proc connect {args} {}
proc disconnect {} {}
proc configparams {args} {}
proc after {args} {}
proc targets {args} {
 if {[lindex $args 0] eq "-set"} {return}
 return [list [dict create target_id 1 jtag_cable_serial 210383B7F02DA]]
}
proc mrd {args} {global memory;return [dict get $memory [expr {[lindex $args end]}]]}
proc mwr {args} {error "Forbidden write"}
proc stop {args} {error "Forbidden CPU stop"}
proc rst {args} {error "Forbidden reset"}
set argv [list fixture 210383B7F02DA]
'''
        text+='if {[catch {source {'+str(REPO/'scripts/probe_rpc_failstop.tcl')+'}} error]} {puts stderr $error;exit 1}\n'
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'probe.tcl';p.write_text(text)
            return subprocess.run(['tclsh',str(p)],capture_output=True,text=True,timeout=3)

    def test_terminal_event_and_limits(self):
        r=self.run_probe('good');self.assertEqual(r.returncode,0,r.stderr)
        self.assertIn('TEST rpc_cancel_terminal_event PASS',r.stdout)
        self.assertIn('worker_reuse_NOT_PROVEN',r.stdout)

    def test_missing_wrong_command_or_message_rejected(self):
        for scenario in ('no_event','wrong_command','wrong_message'):
            with self.subTest(scenario=scenario):
                r=self.run_probe(scenario);self.assertNotEqual(r.returncode,0)
                self.assertNotIn('TEST rpc_cancel_terminal_event PASS',r.stdout)

if __name__=='__main__':unittest.main()
