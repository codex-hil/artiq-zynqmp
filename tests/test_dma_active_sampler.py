"""Active sampler exact inventory and inconclusive controls; LGPL-3.0-or-later."""
import sys,unittest,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from check_dma_observer_active import parse
class Tests(unittest.TestCase):
 def frame(self,count=0,flags=0):
  return 'DMA_ACTIVE_BEGIN\n'+''.join(f'DMA_ACTIVE {i} 0x{a:08x} 0x{v:08x}\n' for i in range(128) for a,v in [(0xa0003000,count),(0xa0003004,flags)])+'DMA_ACTIVE_END\n'
 def test_inconclusive_and_errors(self):
  self.assertEqual(parse(self.frame())['status'],'INCONCLUSIVE_NO_NONZERO_SAMPLE')
  self.assertEqual(parse(self.frame(count=3))['max_outstanding'],3)
  for bad in [self.frame()+self.frame(),self.frame().replace('DMA_ACTIVE_END',''),self.frame(count=128),self.frame(flags=1),self.frame(flags=8)]:
   with self.assertRaises(ValueError):parse(bad)
 def test_actual_tcl_is_bounded_read_only(self):
  mock='''set argv {server 210383B7F02DA}
proc connect {args} {}
proc disconnect {} {}
proc after {args} {}
proc targets {args} {
 if {[lindex $args 0] eq "-set"} {return}
 return [list [dict create jtag_cable_serial 210383B7F02DA target_id 1]]
}
set count 0
proc mrd {args} {
 global count
 if {[lrange $args 0 2] ne {-address-space AP0 -value} || [lindex $args 3] ni {0xa0003000 0xa0003004}} {error unsafe-read}
 incr count
 return 0
}
'''
  mock+='source {'+str(ROOT/'scripts/probe_dma_observer_active.tcl')+'}\nif {$count != 256} {error count}\n'
  r=subprocess.run(['tclsh'],input=mock,text=True,capture_output=True,timeout=5)
  self.assertEqual(r.returncode,0);self.assertFalse(r.stderr,r.stderr)
  self.assertEqual(parse(r.stdout)['status'],'INCONCLUSIVE_NO_NONZERO_SAMPLE')
if __name__=='__main__':unittest.main()
