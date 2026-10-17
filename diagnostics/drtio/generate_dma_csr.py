"""Standalone PS AXI/CSR DMA peripheral RTL; no physical target or firmware.

LGPL-3.0-or-later. Emits control AXI, memory AXI and external CRI ports.
"""
import argparse,json,os
from pathlib import Path
from migen import Module,ClockDomain
from migen.fhdl import verilog
from migen.genlib.resetsync import AsyncResetSynchronizer
from migen.build.xilinx.common import XilinxAsyncResetSynchronizer
from litex.soc.interconnect.axi import AXIInterface
from aux_ps import AuxPS
from dma_csr import DMACSR

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--lab-read-delay-sys-hz',type=int,
        help='Opt in to laboratory delay peripheral; caller-provided actual sys frequency')
    p.add_argument('--lab-read-delay-us',type=int,default=2000)
    a=p.parse_args();out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
    d=Module();d.clock_domains.cd_rtio_rx=ClockDomain('rtio_rx')
    bus=AXIInterface(data_width=64,address_width=49,id_width=6)
    if a.lab_read_delay_sys_hz is None:
        d.submodules.control=c=DMACSR(bus)
    else:
        from dma_read_delay_control import LabDelayedDMACSR
        d.submodules.control=c=LabDelayedDMACSR(bus,sys_clk_hz=a.lab_read_delay_sys_hz,
                                               delay_us=a.lab_read_delay_us)
    d.submodules.ps=ps=AuxPS(extra_banks=[('dma',4,c.csrs)])
    ios={c.fault,c.rtio_reset_request,ps.reset,ps.rx_raw,ps.tx_raw}
    ios.update(c.cri.flatten())
    for interface in (bus,ps.axi):
        for channel in ('aw','ar','w','b','r'):ios.update(getattr(interface,channel).flatten())
    os.chdir(out)
    verilog.convert(d,ios=ios,name='dma_ps_peripheral',special_overrides={
        AsyncResetSynchronizer:XilinxAsyncResetSynchronizer}).write(str(out/'dma_ps_peripheral.v'))
    mapping=c.memory_map(ps.BASE+4*0x800)
    mapping.update({'aux_sram':ps.memory_map()['aux_sram'],
        'aux_registers':ps.memory_map()['registers'],
        'kind':'GENERATED_RTL_AND_MAP_NOT_HARDWARE',
        'scope':'standalone PS AXI/CSR, bounded read engine and external CRI; no Genesys PS/GT pin connection',
        'gray_and_bundled_constraints':'NOT_ADDED','firmware_and_vivado':'NOT_RUN'})
    (out/'csr-map.json').write_text(json.dumps(mapping,indent=2)+'\n')
if __name__=='__main__':main()
