#!/usr/bin/env python3
"""Generate standalone AUX PS integration HDL, LGPL-3.0-or-later."""
import argparse
import json
import hashlib
from migen import Module, ClockDomain
from migen.fhdl import verilog
from migen.build.xilinx.common import xilinx_special_overrides
from aux_ps import AuxPS


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',required=True)
    a=p.parse_args()
    from pathlib import Path
    out=Path(a.output)
    out.mkdir(parents=True,exist_ok=True)
    m=Module()
    clocks=[]
    for name in ('sys','gth_tx','gth_rx'):
        cd=ClockDomain(name)
        setattr(m.clock_domains,'cd_'+name,cd)
        clocks.append(cd.clk)
    m.submodules.aux=aux=AuxPS()
    ios=set(clocks+[aux.reset,aux.tx_raw,aux.rx_raw])
    for channel in (aux.axi.aw,aux.axi.w,aux.axi.b,aux.axi.ar,aux.axi.r):
        ios.update(signal for signal,direction in channel.iter_flat())
    v=verilog.convert(m,ios=ios,name='aux_ps',special_overrides=xilinx_special_overrides)
    (out/'aux_ps.v').write_text(str(v))
    (out/'csr-map.json').write_text(json.dumps(aux.memory_map(),indent=2)+'\n')
    files=('aux_ps.v','csr-map.json')
    (out/'results.json').write_text(json.dumps({'status':'PASS',
        'kind':'HDL_GENERATION_NOT_SYNTHESIS_OR_HARDWARE',
        'sha256':{f:hashlib.sha256((out/f).read_bytes()).hexdigest() for f in files}},indent=2)+'\n')
    print('Standalone AXI AUX HDL generated:',out)


if __name__=='__main__':main()
