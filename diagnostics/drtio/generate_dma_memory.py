"""Standalone AXI drain/CDC RTL, not PS/board integration; LGPL-3.0-or-later."""
import argparse,json,os
from pathlib import Path
from migen import Module,ClockDomain
from migen.fhdl import verilog
from migen.genlib.resetsync import AsyncResetSynchronizer
from migen.build.xilinx.common import XilinxAsyncResetSynchronizer
from litex.soc.interconnect.axi import AXIInterface
from dma_memory_guard import DMAMemoryGuard
from dma_raw_cdc import DMARawCDC

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
    d=Module();d.clock_domains.cd_rtio_rx=ClockDomain('rtio_rx')
    bus=AXIInterface(data_width=64,address_width=49,id_width=6)
    d.submodules.guard=g=DMAMemoryGuard(bus);d.submodules.cross=q=DMARawCDC()
    d.comb += g.source.connect(q.sink)
    ios={g.start,g.finish,g.abort,g.active,g.done,g.failed,g.rejected_start,
         g.reader.base_address.storage,q.reset,q.write_ready,q.read_reset,
         q.source.stb,q.source.ack,q.source.data}
    for channel in (bus.ar,bus.r):ios.update(channel.flatten())
    os.chdir(out)
    verilog.convert(d,ios=ios,name='dma_memory',special_overrides={
        AsyncResetSynchronizer:XilinxAsyncResetSynchronizer}).write(str(out/'dma_memory.v'))
    (out/'scope.json').write_text(json.dumps({'kind':'GENERATED_RTL_NOT_HARDWARE',
        'memory_domain':'sys must remain running until guard.done',
        'consumer_domain':'rtio_rx may pause; restart requires reset handshake',
        'reset_input_minimum':'one sys edge; also assert guard.abort for interrupted trace',
        'alignment_bytes':128,'width_bits':64,'queue_depth':16,
        'gray_constraints':'NOT_ADDED: both FIFO pointer buses need physical CDC constraints',
        'decoder_cri_firmware':'NOT_CONNECTED','vivado_hardware':'NOT_RUN'},indent=2)+'\n')
if __name__=='__main__':main()
