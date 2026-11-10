# SPDX-License-Identifier: LGPL-3.0-or-later
"""Full core/link integration latency, explicit sticky-state fault injection.

Functional reset model, exact Xilinx MultiReg lowering. Not a physical bound.
"""
import json,os,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from migen import ClockDomain,ClockSignal,Signal
from migen.sim import run_simulation,passive
from migen.genlib.resetsync import AsyncResetSynchronizer
from migen.genlib.cdc import MultiReg
from migen.build.xilinx.common import XilinxMultiReg
from test_master_ps_cdc import FunctionalReset
from test_master_csr import AXIMaster
from test_grouped_registered_full_hpm import RegisteredCoordinatorFixture,grouped_fixture
from master_admission_registered import MasterLinkBoundaryRegistered
from master_link_boundary import MasterLinkBoundary
from master_integration import GenesysMasterIntegration
from raw20_codec import Raw20Codec

class AdmissionIntegrationTests(unittest.TestCase):
 def exercise(self,registered):
  ps=SimpleNamespace(inputs={},outputs={})
  root=Path(__file__).resolve().parents[2]
  for line in (root/'evidence/genesys-master-aux-gray-link-2026-11-07/ps-hpm-wrapper-v2/pins.tsv').read_text().splitlines():
   name,direction,left,right=line.split('\t');width=abs(int(left)-int(right))+1 if left and right else 1
   (ps.inputs if direction=='I' else ps.outputs)[name]=Signal(width)
  codec=Raw20Codec()
  with patch('master_dual_ingress.AuxResetControl',RegisteredCoordinatorFixture),patch('master_dual_ingress.AuxResetDomains',side_effect=grouped_fixture),patch('master_link_boundary.MasterLinkBoundary',MasterLinkBoundaryRegistered if registered else MasterLinkBoundary):
   top=GenesysMasterIntegration(ps,codec.channel,ClockSignal('tx_source'),ClockSignal('rx_source'),codec=codec,link_status=SimpleNamespace(reset_done=Signal(reset=1),clock_active=Signal(reset=1),aligned=Signal(reset=1)),guarded_candidate=True)
  top.submodules.codec=codec
  for name in ('pl_source','tx_source','rx_source'):setattr(top.clock_domains,'cd_'+name,ClockDomain(name,reset_less=True))
  top.comb+=ps.outputs['pl_clk0'].eq(ClockSignal('pl_source'))
  bus=SimpleNamespace()
  for channel,names in {'aw':'id addr len size burst lock cache prot qos valid ready','ar':'id addr len size burst lock cache prot qos valid ready','w':'data strb last valid ready','b':'id resp valid ready','r':'id data resp last valid ready'}.items():
   fields={}
   for field in names.split():
    name='maxigp1_'+channel+field;fields[field]=(ps.inputs if name in ps.inputs else ps.outputs)[name]
   setattr(bus,channel,SimpleNamespace(**fields))
  h=AXIMaster(bus);base=0xb0000000;state={'event':None,'traces':{},'done':False}
  @passive
  def observer():
   while True:
    event=state['event']
    if event is not None:state['traces'][event].append({'raw_admit':(yield top.admit),'link_allowed':(yield top.link_boundary.allowed)})
    yield
  def poll(mask,value):
   for _ in range(100):
    status=yield from h.read(base+8)
    if status&mask==value:return
   self.fail('management timeout')
  def open_link():
   yield from h.write(base+4,0);yield from poll(3,3)
   yield from h.write(base+4,2);yield from poll(5,4)
   for _ in range(100):
    if (yield top.link_boundary.allowed):return
    yield
   self.fail('link never admitted')
  def manager():
   yield ps.outputs['pl_resetn0'].eq(1)
   for _ in range(24):yield
   yield from open_link()
   for event in ('progress_fault','shape_fault','reset'):
    state['traces'][event]=[];state['event']=event
    if event=='progress_fault':yield top.progress.fault.eq(1)
    elif event=='shape_fault':yield top.shape_guard.fault.eq(1)
    else:yield from h.write(base+4,1)
    for _ in range(70):yield
    trace=state['traces'][event]
    self.assertTrue(trace and any(x['raw_admit']==0 for x in trace))
    self.assertEqual(trace[-1]['link_allowed'],0)
    first_raw=next(i for i,x in enumerate(trace) if x['raw_admit']==0)
    first_closed=next(i for i,x in enumerate(trace) if x['link_allowed']==0)
    self.assertLessEqual(first_closed-first_raw,5)
    state['event']=None
    if event!='reset':
     yield from h.write(base+4,1);yield from poll(5,1)
     yield from open_link()
   state['done']=True
  clocks={'pl_source':8,'tx_source':14,'rx_source':18,'management':8,'control':8,'ps':8,'sys':14,'rio':14,'rio_phy':14,'rtio_rx':18,'aux_release_ps':8,'aux_release_sys':14,'aux_release_rtio_rx':18}
  for name,crossing in top.csr.ps_cdc.crossings.items():
   for domain,period in zip(crossing._fragment.clock_domains,(14,8) if name in ('b','r') else (8,14)):clocks[domain.name]=period
  run_simulation(top,{'management':manager(),'sys':observer()},clocks,special_overrides={AsyncResetSynchronizer:FunctionalReset,MultiReg:XilinxMultiReg})
  self.assertTrue(state['done'])
  return state['traces']
 def test_baseline_and_registered_fault_reset_withdrawal(self):
  results={name:self.exercise(flag) for name,flag in (('baseline',False),('registered',True))}
  for name,traces in results.items():
   for event,trace in traces.items():
    raw=next(i for i,x in enumerate(trace) if x['raw_admit']==0);closed=next(i for i,x in enumerate(trace) if x['link_allowed']==0)
    print('WITHDRAWAL_EDGES',name,event,'raw_first',raw,'closed_first',closed,'delta_sys_samples',closed-raw)
  if os.environ.get('ADMISSION_TRACE_OUTPUT'):Path(os.environ['ADMISSION_TRACE_OUTPUT']).write_text(json.dumps(results,indent=2)+'\n')
if __name__=='__main__':unittest.main()
