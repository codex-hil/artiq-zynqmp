"""Generate standalone diagnostic satellite RTL. LGPL-3.0-or-later."""
import argparse
import json
import os
from pathlib import Path
from types import SimpleNamespace
from migen import Signal
from migen.fhdl import verilog
from satellite_backend import SatelliteBackend


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--dma', action='store_true', help='Same-clock AXI DMA/CRI lab ports, not PS integration')
    parser.add_argument('--fine-ts-width', type=int, default=0, choices=(0,3))
    args = parser.parse_args()
    link = SimpleNamespace(**{name: Signal(width, name=name) for name, width in (
        ('tx_rt_frame', 1), ('tx_rt_data', 16),
        ('rx_rt_frame', 1), ('rx_rt_data', 16))})
    ttl_out, ttl_in = Signal(name='ttl_out'), Signal(name='ttl_in')
    bus=None
    if args.dma:
        from litex.soc.interconnect.axi import AXIInterface
        bus=AXIInterface(data_width=64,address_width=49,id_width=6)
    dut = SatelliteBackend(link, ttl_out, ttl_in,
                           glbl_fine_ts_width=args.fine_ts_width, dma_membus=bus)
    ios = set(vars(link).values()) | {ttl_out, ttl_in, dut.tsc.coarse_ts}
    ios.update(getattr(dut.async_errors, field) for field, _ in dut.async_errors.layout)
    if args.dma:
        for channel in (bus.ar,bus.r):ios.update(channel.flatten())
        ios.update([dut.cri_switch.selected.storage,dut.dma.enable.re,
                    dut.dma.enable.w,dut.dma.dma.base_address.storage,
                    dut.dma.time_offset.time_offset.storage,
                    dut.dma.cri_master.error.re,dut.dma.cri_master.error.w,
                    dut.dma.dma.wb_reader.bus_error.status])
    args.output = args.output.resolve()
    args.output.mkdir(parents=True, exist_ok=True)
    # Migen emits ROM initialization files relative to the current directory.
    os.chdir(args.output)
    verilog.convert(dut, ios=ios, name='satellite_backend').write(
        str(args.output / 'satellite_backend.v'))
    (args.output / 'scope.json').write_text(json.dumps({
        'kind': 'generated RTL, not hardware validation',
        'dma':args.dma,'global_fine_ts_width':args.fine_ts_width,
        'dma_base_alignment_bytes':128 if args.dma else None,
        'dma_scope':'same-clock AXI read/CRI switch only; quiescent ownership changes; no PS CDC, DDMA firmware or active reset qualification',
        'clock_domain': 'sys', 'channel_0': 'TTL output', 'channel_1': 'TTL input',
        'lane_count': 8, 'fifo_depth': 128,
        'transport_requirement': 'packet frame/data synchronous to sys',
        'external_synchronization': 'NOT_RUN', 'aux_reset_service': 'NOT_IMPLEMENTED'
    }, indent=2) + '\n')


if __name__ == '__main__':
    main()
