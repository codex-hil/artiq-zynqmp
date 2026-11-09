#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Export isolated PS-adapter boundary RTL; PS hard primitive remains external."""
import argparse,json,hashlib,os
from pathlib import Path
from types import SimpleNamespace
from migen import Signal
from migen.fhdl import verilog
from migen.build.xilinx.common import xilinx_special_overrides
from master_physical_assembly import MasterPhysicalAssembly

p=argparse.ArgumentParser();p.add_argument('output',type=Path)
p.add_argument('--guarded-candidate',action='store_true');args=p.parse_args()
root=Path(__file__).resolve().parents[3]
ps=SimpleNamespace(inputs={},outputs={})
pins=root/'evidence/genesys-master-aux-gray-link-2026-11-07/ps-hpm-wrapper-v2/pins.tsv'
for line in pins.read_text().splitlines():
 name,direction,left,right=line.split('\t')
 width=abs(int(left)-int(right))+1 if left and right else 1
 (ps.inputs if direction=='I' else ps.outputs)[name]=Signal(width,name=name)
pads=SimpleNamespace(**{name:Signal(name='sfp_'+name) for name in ('rxp','rxn','txp','txn')})
ref=SimpleNamespace(p=Signal(name='ref_p'),n=Signal(name='ref_n'))
if args.guarded_candidate:
 import importlib.util
 checker=root/'diagnostics/drtio/role-reversal/check-interface-manifest.py'
 spec=importlib.util.spec_from_file_location('interface_checker',checker)
 module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 module.validate(json.loads((checker.parent/'interface-manifest-v1.json').read_text()))
top=MasterPhysicalAssembly(ps,pads,ref,guarded_candidate=args.guarded_candidate)
ios=set(vars(pads).values())|set(vars(ref).values())|{top.sfp_tx_disable}
used={name:s for collection in (ps.inputs,ps.outputs) for name,s in collection.items()
      if name.startswith(('maxigp0_','maxigp1_','maxihpm0_','maxihpm1_')) or name in ('pl_clk0','pl_resetn0')}
for index,signal in enumerate(top.local_outputs):
 signal.name_override=f'local_ttl{index}'
 ios.add(signal)
ios|=set(used.values())
args.output.mkdir(parents=True,exist_ok=True)
from master_cdc_inventory import collect
fragment=top.get_fragment()
source_notes={top.core.local.sed_spread_enable:'Internal undriven initialized0 control; not external clock',
 top.core.ingress.coordinator.reset:'Control FSM combinational reset output; explicit reset protocol',
 top.core.ingress.coordinator.admit:'Control FSM combinational admit output; ready/request dependent',
 top.phy.link_status.reset_done:'Vendor GTH rxdone output; physical source/CDC qualification OPEN',
 top.phy.link_status.clock_active:'Vendor userclk RX active output; RX-clocked sticky status, NOT watchdog'}
inventory=collect(fragment,top,source_notes)
(args.output/'cdc-inventory.json').write_text(json.dumps(inventory,indent=2)+'\n')
# Observe the existing vendor lowering without replacing its implementation.
from migen.genlib.cdc import MultiReg
from migen.fhdl.tools import list_signals
lowered=[]
reset_lowered=[]
from migen.genlib.resetsync import AsyncResetSynchronizer
from migen.fhdl.specials import Instance
original_multireg=xilinx_special_overrides[MultiReg]
class ObservedMultiReg:
 @staticmethod
 def lower(special):
  implementation=original_multireg.lower(special)
  lowered.append((special,implementation))
  return implementation
original_reset=xilinx_special_overrides[AsyncResetSynchronizer]
class ObservedReset:
 @staticmethod
 def lower(special):
  implementation=original_reset.lower(special)
  cells=sorted(implementation._fragment.specials,key=lambda cell:cell.duid)
  reset_lowered.append((special,cells))
  return implementation
overrides=dict(xilinx_special_overrides);overrides[MultiReg]=ObservedMultiReg
overrides[AsyncResetSynchronizer]=ObservedReset
domains=list(fragment.clock_domains)
result=verilog.convert(fragment,ios=ios,name='master_physical_candidate',special_overrides=overrides)
endpoint_rows=[]
for special,implementation in lowered:
 endpoint_rows.append({'bits':len(special.i),'destination':special.odomain,
  'input_signals':sorted(result.ns.get_name(s) for s in list_signals(special.i)),
  'output_signals':sorted(result.ns.get_name(s) for s in list_signals(special.o)),
  'stage_registers':[result.ns.get_name(r) for r in implementation.regs],
  'requested_reset':int(special.reset),
  'lowered_register_reset':[r.reset.value for r in implementation.regs]})
import re
aliases=dict(re.findall(r'assign\s+(\w+)\s*=\s*(\w+)\s*;',result.main_source))
def chain(name):
 visited=[]
 while name in aliases and name not in visited:
  visited.append(name);name=aliases[name]
 return visited+[name]
endpoints={'status':'EMITTED_RTL_NAMES_ONLY_NOT_NETLIST_TIMING_ENDPOINTS',
  'multiregs':endpoint_rows,
 'clock_aliases':{cd.name:chain(result.ns.get_name(cd.clk)) for cd in domains},
 'limits':['No get_cells/get_pins post-synthesis binding','No reset polarity/initialization waiver','No constraints generated']}
reset_rows=[]
for special,cells in reset_lowered:
 entries=[]
 for cell in cells:
  assert isinstance(cell,Instance) and cell.of=='FDPE'
  params={item.name:item.value.value for item in cell.items if isinstance(item,Instance.Parameter)}
  pin_expr={item.name:verilog._printexpr(result.ns,item.expr)[0] for item in cell.items if isinstance(item,Instance._IO)}
  entries.append({'rtl_instance':result.ns.get_name(cell),'primitive':cell.of,'parameters':params,'pins':pin_expr})
 reset_rows.append({'domain':special.cd.name,'clock_alias_chain':chain(result.ns.get_name(special.cd.clk)),
  'asynchronous_assert_expression':verilog._printexpr(result.ns,special.async_reset)[0],
  'reset_output':result.ns.get_name(special.cd.rst),'cells':entries})
endpoints['reset_synchronizers']=reset_rows
(args.output/'cdc-endpoints.json').write_text(json.dumps(endpoints,indent=2)+'\n')
original=Path.cwd()
try:
 os.chdir(args.output.resolve())
 result.write('master_physical_candidate.v')
finally:
 os.chdir(original)
report={'status':'RTL_EXPORT_ONLY_PS_ADAPTER_BOUNDARY','ps_export_sha256':hashlib.sha256(pins.read_bytes()).hexdigest(),
        'guarded_candidate':args.guarded_candidate,
        'runtime_capability_granted':False,
        'ports':{name:{'rtl_name':result.ns.get_name(signal),'bits':len(signal)} for name,signal in used.items()},
        'local_outputs':[result.ns.get_name(signal) for signal in top.local_outputs],
        'limits':['PS hardIP external; adapter boundary signals only','No XDC or synthesis/timing/physical qualification']}
report['interface_manifest_sha256']=hashlib.sha256((root/'diagnostics/drtio/role-reversal/interface-manifest-v1.json').read_bytes()).hexdigest() if args.guarded_candidate else None
report['generated_sha256']={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in args.output.iterdir() if f.suffix in ('.v','.init') or f.name in ('cdc-inventory.json','cdc-endpoints.json')}
report['assembly_source_sha256']={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in ('diagnostics/drtio/master_integration.py','diagnostics/drtio/master_physical_assembly.py','diagnostics/drtio/master_cdc_inventory.py','diagnostics/drtio/role-reversal/export-physical-assembly.py')}
(args.output/'export.json').write_text(json.dumps(report,indent=2)+'\n')
print('MASTER_PHYSICAL_ASSEMBLY_RTL_EXPORT_PASS')
