# SPDX-License-Identifier: LGPL-3.0-or-later
import subprocess,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class Tests(unittest.TestCase):
 def run_case(self,rows,value='0x10000',args=('server','210383B7F02DA','7','0')):
  text='''set reads 0
proc connect {args} {}
proc disconnect {} {puts DISCONNECTED}
proc targets {args} {global rows; if {[lindex $args 0] eq "-set"} {return}; return $rows}
proc mrd {args} {global reads mock_reply; if {$args ne "-address-space AP0 -value 0xffd80000 1"} {error "wrong access"}; incr reads;return $mock_reply}
'''
  text+='set rows {'+rows+'}\nset mock_reply {'+value+'}\nset argv {'+' '.join(args)+'}\n'
  text+='set failed [catch {source {'+str(ROOT/'scripts/probe_pmu_sleep_status.tcl')+'}} msg]\nputs "FAILED=$failed READS=$reads MSG=$msg"\n'
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'mock.tcl';p.write_text(text);return subprocess.check_output(['tclsh',str(p)],text=True)
 def test_exact_single_read_and_cleanup(self):
  text=self.run_case('{name PSU target_id 4 jtag_cable_serial 210383B7F02DA}')
  self.assertIn('PMU_SLEEP_STATUS 00000000 00000007 00010000',text);self.assertIn('FAILED=0 READS=1',text);self.assertIn('DISCONNECTED',text)
 def test_identity_refusals_no_reads(self):
  for rows in ['', '{name PSU target_id 4 jtag_cable_serial OTHER}', '{name PMU target_id 4 jtag_cable_serial 210383B7F02DA}', '{name PSU target_id 4 jtag_cable_serial 210383B7F02DA} {name PSU target_id 5 jtag_cable_serial 210383B7F02DA}']:
   self.assertIn('FAILED=1 READS=0',self.run_case(rows))
 def test_bad_response_not_retried(self):
  for value in ['', '1 2','-1','4294967296','not-a-word']:
   text=self.run_case('{name PSU target_id 4 jtag_cable_serial 210383B7F02DA}',value)
   self.assertIn('FAILED=1 READS=1',text);self.assertIn('DISCONNECTED',text)
 def test_wrong_args_no_connection_access(self):
  for args in [('server','OTHER','7','0'),('server','210383B7F02DA','0','0'),('server','210383B7F02DA','-1','0'),('server','210383B7F02DA','7','0','extra')]:
   self.assertIn('FAILED=1 READS=0',self.run_case('',args=args))
if __name__=='__main__':unittest.main()
