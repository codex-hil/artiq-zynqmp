"""Generate standalone diagnostic satellite RTL. LGPL-3.0-or-later."""
import argparse
import json
from pathlib import Path
from types import SimpleNamespace
from migen import Signal
from migen.fhdl import verilog
from satellite_backend import SatelliteBackend


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    link = SimpleNamespace(**{name: Signal(width, name=name) for name, width in (
        ('tx_rt_frame', 1), ('tx_rt_data', 16),
        ('rx_rt_frame', 1), ('rx_rt_data', 16))})
    ttl_out, ttl_in = Signal(name='ttl_out'), Signal(name='ttl_in')
    dut = SatelliteBackend(link, ttl_out, ttl_in)
    ios = set(vars(link).values()) | {ttl_out, ttl_in, dut.tsc.coarse_ts}
    ios.update(getattr(dut.async_errors, field) for field, _ in dut.async_errors.layout)
    args.output.mkdir(parents=True, exist_ok=True)
    verilog.convert(dut, ios=ios, name='satellite_backend').write(
        str(args.output / 'satellite_backend.v'))
    (args.output / 'scope.json').write_text(json.dumps({
        'kind': 'generated RTL, not hardware validation',
        'clock_domain': 'sys', 'channel_0': 'TTL output', 'channel_1': 'TTL input',
        'lane_count': 8, 'fifo_depth': 128,
        'transport_requirement': 'packet frame/data synchronous to sys',
        'external_synchronization': 'NOT_RUN', 'aux_reset_service': 'NOT_IMPLEMENTED'
    }, indent=2) + '\n')


if __name__ == '__main__':
    main()
