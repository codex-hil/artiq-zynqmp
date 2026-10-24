"""Generate an out-of-context integration build; no pins, GTs or bitstream."""
import argparse, hashlib, importlib.util, json, os, re
from pathlib import Path
import env
from migen import *
from migen.fhdl import verilog
from litex.build.xilinx.common import xilinx_special_overrides
from dsp import Generator
from envelope import EnvelopePlayer, EnvelopeStage
from registers import Registers
from rtio_cdc import EnvelopeRTIOBridge

p=argparse.ArgumentParser(description=__doc__);p.add_argument('output',type=Path)
p.add_argument('--rtlink',type=Path,default=Path('/srv/codex-hil-data/artiq-zynqmp/reference/artiq/artiq/gateware/rtio/rtlink.py'))
a=p.parse_args();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
spec=importlib.util.spec_from_file_location('rtlink',a.rtlink);rl=importlib.util.module_from_spec(spec);spec.loader.exec_module(rl)
m=Module()
for name in ['net','jesd','rio_phy']:setattr(m.clock_domains,'cd_'+name,ClockDomain(name))
m.submodules.generator=g=Generator();m.submodules.player=e=EnvelopePlayer()
m.submodules.stage=s=EnvelopeStage(g.samples,e)
m.submodules.registers=r=ClockDomainsRenamer('net')(Registers(g,e))
m.submodules.bridge=b=EnvelopeRTIOBridge(e,rl)
groups={
 'net':([r.address,r.wdata,r.write,r.strobe,m.cd_net.rst],[r.rdata,r.ack,r.err]),
 'rio_phy':([b.enable,b.reset,b.rtlink.o.stb,b.rtlink.o.data,m.cd_rio_phy.rst],[b.ready,b.rtlink.o.busy,b.rtlink.i.stb,b.rtlink.i.data]),
 'jesd':([m.cd_jesd.rst],[v for ch in s.samples for pair in ch for v in pair])}
ios=set(v for ins,outs in groups.values() for v in ins+outs)
for name in groups:ios.add(getattr(m,'cd_'+name).clk)
v=verilog.convert(m,ios=ios,name='phaser_rtio',special_overrides=xilinx_special_overrides)
v.main_source,count=re.subn(r'(reg \[95:0\] envelope_ram\[0:255\];)',r'(* ram_style = "block" *) \1',v.main_source)
assert count==1
os.chdir(out);v.write('phaser_rtio.v')
tcl=['set_param general.maxThreads 4','read_verilog phaser_rtio.v',
     'synth_design -top phaser_rtio -part xcau15p-ffvb676-2-i -mode out_of_context -flatten_hierarchy rebuilt']
for name,(ins,outs) in groups.items():
 period=1000/153.6 if name=='jesd' else 8
 tcl.append(f'create_clock -name {name} -period {period:.9f} [get_ports {v.ns.get_name(getattr(m,"cd_"+name).clk)}]')
 for direction,signals in [('input',ins),('output',outs)]:
  ports=' '.join('{'+v.ns.get_name(x)+('[*]' if len(x)>1 else '')+'}' for x in signals)
  for bound,value in [('max',1),('min',0.2 if direction=='input' else 0)]:tcl.append(f'set_{direction}_delay -clock {name} -{bound} {value} [get_ports [list {ports}]]')
tcl.append('write_checkpoint -force synth.dcp')
tcl.append(Path(__file__).with_name('rtio_constraints.tcl').read_text())
tcl += ['opt_design','place_design','route_design',
        'report_timing_summary -report_unconstrained -file timing.rpt',
        'report_cdc -details -file cdc.rpt','report_bus_skew -file bus-skew.rpt',
        'report_drc -file drc.rpt','report_utilization -file utilization.rpt',
        'write_checkpoint -force routed.dcp',
        'if {[llength [get_timing_paths -delay_type max -slack_lesser_than 0]] || [llength [get_timing_paths -delay_type min -slack_lesser_than 0]]} {error "Timing failure"}']
(out/'build.tcl').write_text('\n'.join(tcl)+'\n')
(out/'inputs-sha256.json').write_text(json.dumps({f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(out.iterdir()) if f.is_file()},indent=2)+'\n')
(out/'rtlink-source.json').write_text(json.dumps({'path':str(a.rtlink),'sha256':hashlib.sha256(a.rtlink.read_bytes()).hexdigest()},indent=2)+'\n')
print(out)
