"""Diagnostic inactive AXI request controls; LGPL-3.0-or-later."""
import sys,unittest
from pathlib import Path
from types import SimpleNamespace
from migen import Module,Signal,ClockDomain
from migen.fhdl import verilog
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'diagnostics/ddr'))
from no_ddr_master import disable_pl_masters
class Tests(unittest.TestCase):
 def test_explicit_tieoffs(self):
  m=Module();m.clock_domains.cd_sys=ClockDomain('sys')
  inputs={f'saxigp{p}_{ch}valid':Signal(name_override=f'saxigp{p}_{ch}valid') for p in (2,3) for ch in ('ar','aw','w')}
  names=disable_pl_masters(m,SimpleNamespace(inputs=inputs))
  rtl=str(verilog.convert(m,ios=set(inputs.values())))
  self.assertEqual(len(names),6)
  for n in names:self.assertIn("assign "+n+" = 1'd0;",rtl)
 def test_missing_channels_reject(self):
  for inputs in ({},{'saxigp2_arvalid':Signal()},{'saxi_unknown_arvalid':Signal()}):
   with self.assertRaises(ValueError):disable_pl_masters(Module(),SimpleNamespace(inputs=inputs))
if __name__=='__main__':unittest.main()
