"""Generate decoded-link satellite transport RTL; LGPL-3.0-or-later."""
import argparse
import json
import os
from pathlib import Path
from types import SimpleNamespace
from migen import Module, Signal, ClockDomain
from migen.fhdl import verilog
from satellite_transport import SatelliteTransport


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();a.output=a.output.resolve();a.output.mkdir(parents=True,exist_ok=True)
    d=Module()
    for name in ('sys','rtio_rx','gth_tx'):
        setattr(d.clock_domains,'cd_'+name,ClockDomain(name))
    endpoint=SimpleNamespace(
        rx=SimpleNamespace(rt_frame=Signal(name='rx_frame'),rt_data=Signal(16,name='rx_data')),
        tx=SimpleNamespace(rt_frame=Signal(name='tx_frame'),rt_data=Signal(16,name='tx_data')),
        rx_ready=Signal(name='rx_ready'))
    output,input_pin=Signal(name='ttl_out'),Signal(name='ttl_in')
    d.submodules.transport=t=SatelliteTransport(endpoint,output,input_pin)
    ios={endpoint.rx.rt_frame,endpoint.rx.rt_data,endpoint.rx_ready,
         endpoint.tx.rt_frame,endpoint.tx.rt_data,output,input_pin,
         t.tsc_load_count,t.reply_fault}
    for cd in (d.cd_sys,d.cd_rtio_rx,d.cd_gth_tx):ios.update((cd.clk,cd.rst))
    os.chdir(a.output)
    verilog.convert(d,ios=ios,name='satellite_transport').write(str(a.output/'satellite_transport.v'))
    (a.output/'scope.json').write_text(json.dumps({
        'kind':'generated RTL, not routed or hardware validated',
        'rx_rtio_clock':'rtio_rx','reply_tx_clock':'gth_tx','management_clock':'sys',
        'reset_requirement':'common assertion across all three domains',
        'tsc_ack_requirement':'firmware observes a new actual load counter, no ACK implemented here',
        'reply_fault':'sticky RX-domain fatal diagnostic; synchronize before PS use',
        'max_reply_bytes':128,'production_satellite':'NOT_IMPLEMENTED'
    },indent=2)+'\n')


if __name__=='__main__':main()
