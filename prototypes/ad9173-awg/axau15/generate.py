"""AXAU15 candidate, dedicated GBTCLK0, no hardware access.
Requires board/revision/clock-population validation before programming.
"""
import argparse
import json
import os
from pathlib import Path
import sys
from importlib import import_module
from migen import *
from migen.fhdl import verilog
from migen.genlib.cdc import BusSynchronizer, MultiReg
from migen.genlib.resetsync import AsyncResetSynchronizer
from litex.build.xilinx.common import xilinx_special_overrides
from liteiclink.serdes.gth4_ultrascale import GTH4, GTH4QuadPLL
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'gateware'))
DualLink = import_module('generate-link').DualLink

class AXAU15(Module):
    def __init__(self, spi_only=False):
        self.clock_domains.cd_sys = ClockDomain('sys')
        sys_p, sys_n = Signal(name='sys_p'), Signal(name='sys_n')
        raw, eos = Signal(), Signal()
        self.specials += [
            Instance('IBUFDS', i_I=sys_p, i_IB=sys_n, o_O=raw),
            Instance('BUFGCE_DIV', p_BUFGCE_DIVIDE=2, i_I=raw, i_CE=1,
                     i_CLR=0, o_O=self.cd_sys.clk),
            Instance('STARTUPE3', o_EOS=eos, i_GSR=0, i_GTS=0,
                     i_KEYCLEARB=1, i_PACK=0, i_USRCCLKO=0, i_USRCCLKTS=1,
                     i_USRDONEO=1, i_USRDONETS=0, i_DO=0, i_DTS=15,
                     i_FCSBO=1, i_FCSBTS=1),
            AsyncResetSynchronizer(self.cd_sys, ~eos)]
        self.ios = {sys_p, sys_n}
        spi = {n: Signal(name=n) for n in
               ('sck', 'mosi', 'miso', 'cs_dac', 'cs_clock', 'spi_en')}
        self.ios.update(spi.values())
        amplitude = Signal(16)
        self.specials += Instance('spi_console', p_INITIAL_PAYLOAD=0, i_clk=self.cd_sys.clk,
            i_spi_en=spi['spi_en'], i_miso=spi['miso'],
            o_sck=spi['sck'], o_mosi=spi['mosi'], o_cs_dac=spi['cs_dac'],
            o_cs_clock=spi['cs_clock'], o_payload_amp=amplitude)
        self.pll_config = None
        if spi_only:
            return
        ref_p, ref_n, ref = Signal(name='ref_p'), Signal(name='ref_n'), Signal()
        self.ios.update((ref_p, ref_n))
        self.specials += Instance('IBUFDS_GTE4', i_I=ref_p, i_IB=ref_n,
                                 i_CEB=0, o_O=ref)
        self.submodules.qpll = qpll = GTH4QuadPLL(ref, 245.76e6, 6.144e9)
        self.pll_config = qpll.config
        phys = []
        for n in range(4):
            tx = Record([('p', 1), ('n', 1)], name=f'tx{n}')
            rx = Record([('p', 1), ('n', 1)])
            gth = GTH4(qpll, tx, rx, 100e6, data_width=40,
                       tx_buffer_enable=True, rx_buffer_enable=True,
                       clock_aligner=False, pll_master=n == 0)
            gth.n = n
            gth.add_stream_endpoints()
            gth = ClockDomainsRenamer({'tx': f'jesd_phy{n}_tx',
                                      'rx': f'jesd_phy{n}_rx'})(gth)
            gth.gth_params.update(i_TX8B10BEN=1, i_TX8B10BBYPASS=0,
                i_TXDATA=gth.sink.data, i_TXCTRL0=0, i_TXCTRL1=0,
                i_TXCTRL2=gth.sink.ctrl, i_TXPRBSSEL=0, i_TXPRBSFORCEERR=0)
            setattr(self.submodules, f'gt{n}', gth)
            self.comb += [gth.rx_enable.eq(0), rx.p.eq(0), rx.n.eq(0)]
            phys.append(gth)
            self.ios.update(tx.flatten())
        self.clock_domains.cd_jesd = ClockDomain('jesd')
        self.comb += [self.cd_jesd.clk.eq(phys[0].cd_tx.clk),
                      self.cd_jesd.rst.eq(ResetSignal('jesd_phy0_tx'))]
        self.submodules.link = link = DualLink(phys, subclass=0, hd=1, did=0x61)
        ready = Signal(4)
        for n, phy in enumerate(phys):
            self.specials += MultiReg(phy.tx_ready, ready[n], 'jesd')
        self.comb += [link.enable.eq(ready == 15), link.jref.eq(0)]
        for n in range(2):
            pads = Record([('p', 1), ('n', 1)], name=f'sync{n}')
            self.specials += Instance('IBUFDS', p_DIFF_TERM='TRUE',
                i_I=pads.p, i_IB=pads.n, o_O=link.jsync[n])
            self.ios.update(pads.flatten())
        # Coherent bus handshake; bit15 is always sample sign, never PRBS.
        self.submodules.samples = samples = BusSynchronizer(16, 'sys', 'jesd')
        self.comb += samples.i.eq(amplitude)
        link.drive_payload(samples.o, self)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--spi-only', action='store_true')
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    os.chdir(out)  # Migen memory initialization files must accompany Verilog.
    dut = AXAU15(args.spi_only)
    verilog.convert(dut, ios=dut.ios, name='axau15_awg',
                    special_overrides=xilinx_special_overrides).write('axau15_awg.v')
    (out / 'target.json').write_text(json.dumps({
        'board': 'AXAU15', 'ordering_code': 'XCAU15P-2FFVB676I',
        'candidate_part': 'xcau15p-ffvb676-2-i', 'spi_only': args.spi_only,
        'qpll': dut.pll_config, 'physical_validation': 'NOT_RUN'}, indent=2)+'\n')
