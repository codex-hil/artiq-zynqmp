# SPDX-License-Identifier: LGPL-3.0-or-later
"""Local reset alternative: explicit contract and digital policy tests only."""
import itertools,unittest
from types import SimpleNamespace
from migen import Module,Signal,ClockDomain
from migen.sim import run_simulation
from migen.genlib.cdc import MultiReg
from migen.build.xilinx.common import XilinxMultiReg
from master_link_local_reset import MasterLinkLocalReset

def ports():
 return (SimpleNamespace(**{n:Signal() for n in ('rx_reset','rx_reset_done','rx_clock_active','word_aligned')}),
         SimpleNamespace(**{n:Signal() for n in ('reset_done','clock_active','aligned')}))
class LocalResetTests(unittest.TestCase):
 def test_confirmation_and_removed_path(self):
  for flag in (False,None,1):
   codec,status=ports()
   with self.assertRaises(ValueError):
    MasterLinkLocalReset(codec,Signal(),Signal(),status,parent_reset_contract_confirmed=flag)
  codec,status=ports();request=Signal();d=MasterLinkLocalReset(codec,Signal(),request,status,parent_reset_contract_confirmed=True)
  self.assertIs(d.gt_reset_request,request)
  self.assertEqual(len(d._fragment.specials),4)
  self.assertFalse(any(s.i is request for s in d._fragment.specials))
 def test_source_policy_is_relaxation_not_arbitrary_equivalence(self):
  differences=[]
  for permit,requested,reset in itertools.product((0,1),repeat=3):
   old=permit & (1-requested) & (1-reset);new=permit & (1-reset)
   self.assertLessEqual(old,new)
   if old!=new:differences.append((permit,requested,reset))
  self.assertEqual(differences,[(1,1,0)])
 def test_held_reset_stale_permit_clear_and_fresh_admission_exact_lowering(self):
  d=Module();d.clock_domains.cd_sys=ClockDomain('sys')
  codec,status=ports();admit=Signal();request=Signal(reset=1)
  d.submodules.boundary=b=MasterLinkLocalReset(codec,admit,request,status,parent_reset_contract_confirmed=True)
  def test():
   self.assertEqual((yield b.allowed),0)
   yield d.cd_sys.rst.eq(1)
   # Even a stale/high input permit cannot bypass asserted local reset.
   yield admit.eq(1)
   for _ in range(6):yield
   self.assertEqual((yield b.allowed),0)
   yield admit.eq(0)
   for _ in range(4):yield
   yield request.eq(0);yield d.cd_sys.rst.eq(0)
   for _ in range(4):yield
   self.assertEqual((yield b.allowed),0)
   yield admit.eq(1)
   for _ in range(5):yield
   self.assertEqual((yield b.allowed),1)
   yield request.eq(1);yield d.cd_sys.rst.eq(1)
   yield;yield
   self.assertEqual((yield b.allowed),0)
  run_simulation(d,test(),clocks={'sys':14},special_overrides={MultiReg:XilinxMultiReg})
if __name__=='__main__':unittest.main()
