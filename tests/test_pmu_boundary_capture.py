"""PMU live record capture controls, no HW; LGPL-3.0-or-later."""
import sys,subprocess,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from pmu_boundary_candidate import parse
class Tests(unittest.TestCase):
 def test_real_tcl_fixed_reads(self):
  script='''set argv {server 210383B7F02DA}
proc connect {args} {}
proc disconnect {} {}
proc after {args} {}
proc targets {args} {
 if {[lindex $args 0] eq "-set"} {return}
 return [list [dict create jtag_cable_serial 210383B7F02DA target_id 1]]
}
set reads 0
proc mrd {args} {
 global reads
 incr reads
 if {$args eq {-address-space AP0 -value 0xffdd7cf4}} {return 2}
 if {$args eq {-address-space AP0 -value 0xffdd7cf4 8}} {return {2 0x504d5542 1 1 0 0x7f 0 0}}
 error wrong-read
}
'''
  script+='source {'+str(ROOT/'scripts/probe_pmu_boundary.tcl')+'}\nif {$reads != 12} {error wrong-count}\n'
  r=subprocess.run(['tclsh'],input=script,text=True,capture_output=True,timeout=5)
  self.assertEqual(r.returncode,0);self.assertFalse(r.stderr,r.stderr);self.assertEqual(parse(r.stdout)['coherent_samples'],4)
  for text in [r.stdout+r.stdout,r.stdout.replace('PMU_BOUNDARY_END',''),r.stdout.replace('word4 0x00000000','word4 0x00000001'),r.stdout.replace('after 0x00000002','after 0x00000004')]:
   with self.assertRaises(ValueError):parse(text)
 def test_one_torn_sample_not_treated_as_coherent(self):
  rows=['PMU_BOUNDARY_BEGIN']
  for s in range(4):
   vals=[2,2,0x504d5542,1,8,0,0x7f,0,0,4 if s==0 else 2]
   rows += [f'PMU_BOUNDARY {s} {n} 0x{v:08x}' for n,v in zip(['before']+[f'word{i}' for i in range(8)]+['after'],vals)]
  rows+=['PMU_BOUNDARY_END'];r=parse('\n'.join(rows));self.assertEqual(r['coherent_samples'],3);self.assertFalse(r['snapshots'][0]['coherent'])
if __name__=='__main__':unittest.main()
