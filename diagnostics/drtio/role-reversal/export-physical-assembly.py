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

p=argparse.ArgumentParser();p.add_argument('output',type=Path);args=p.parse_args()
root=Path(__file__).resolve().parents[3]
ps=SimpleNamespace(inputs={},outputs={})
pins=root/'evidence/genesys-master-aux-gray-link-2026-11-07/ps-hpm-wrapper-v2/pins.tsv'
for line in pins.read_text().splitlines():
 name,direction,left,right=line.split('\t')
 width=abs(int(left)-int(right))+1 if left and right else 1
 (ps.inputs if direction=='I' else ps.outputs)[name]=Signal(width,name=name)
pads=SimpleNamespace(**{name:Signal(name='sfp_'+name) for name in ('rxp','rxn','txp','txn')})
ref=SimpleNamespace(p=Signal(name='ref_p'),n=Signal(name='ref_n'))
top=MasterPhysicalAssembly(ps,pads,ref)
ios=set(vars(pads).values())|set(vars(ref).values())|{top.sfp_tx_disable}
used={name:s for collection in (ps.inputs,ps.outputs) for name,s in collection.items()
      if name.startswith(('maxigp0_','maxigp1_','maxihpm0_','maxihpm1_')) or name in ('pl_clk0','pl_resetn0')}
for index,signal in enumerate(top.local_outputs):
 signal.name_override=f'local_ttl{index}'
 ios.add(signal)
ios|=set(used.values())
args.output.mkdir(parents=True,exist_ok=True)
result=verilog.convert(top,ios=ios,name='master_physical_candidate',special_overrides=xilinx_special_overrides)
original=Path.cwd()
try:
 os.chdir(args.output.resolve())
 result.write('master_physical_candidate.v')
finally:
 os.chdir(original)
report={'status':'RTL_EXPORT_ONLY_PS_ADAPTER_BOUNDARY','ps_export_sha256':hashlib.sha256(pins.read_bytes()).hexdigest(),
        'ports':{name:{'rtl_name':result.ns.get_name(signal),'bits':len(signal)} for name,signal in used.items()},
        'local_outputs':[result.ns.get_name(signal) for signal in top.local_outputs],
        'limits':['PS hardIP external; adapter boundary signals only','No XDC or synthesis/timing/physical qualification']}
(args.output/'export.json').write_text(json.dumps(report,indent=2)+'\n')
print('MASTER_PHYSICAL_ASSEMBLY_RTL_EXPORT_PASS')
