#!/usr/bin/env python3
"""Separate PS-readable raw GTH diagnostic, not a DRTIO satellite."""
import argparse
import json
import sys
import shutil
from pathlib import Path
from migen import Module, Signal, ClockDomain, Instance, Cat, ClockSignal
from migen.genlib.cdc import MultiReg
from migen.genlib.resetsync import AsyncResetSynchronizer
from migen.build.generic_platform import Pins, Subsignal, IOStandard
from misoc.interconnect import csr_bus, wishbone2csr
from litex.soc.interconnect.axi import AXIInterface, AXI2Wishbone
from litex.soc.interconnect import wishbone
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'boards/genesys_zu-5ev/1_gateware'))
from gateware import ThisPlatform
from local_rtio import connect_ps_hpm0, CSR_BASE
from monitor import Monitor


class DiagnosticPlatform(ThisPlatform):
    def copy_ips(self, build_dir, subdir='ip'):
        copied = set()
        for source in self.ips:
            source = Path(source)
            relative = Path(subdir) / source.stem / source.name
            destination = Path(build_dir) / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            data = source.read_text()
            if data.lstrip().startswith('{'):
                xci = json.loads(data)
                # Vivado 2025.2 stores generation paths relative to the XCI.
                # Relocate only the copied instance, never its original.
                xci['ip_inst']['gen_directory'] = './'
                xci['ip_inst']['parameters']['runtime_parameters']['OUTPUTDIR'][0]['value'] = './'
                destination.write_text(json.dumps(xci, indent=2)+'\n')
            else:
                shutil.copyfile(source, destination)
            copied.add(str(relative))
        return copied


class Diagnostic(Module):
    def __init__(self, platform, forward_rx_clock=False):
        self.clock_domains.cd_sys = ClockDomain('sys')
        self.clock_domains.cd_gth_rx = ClockDomain('gth_rx')
        self.clock_domains.cd_gth_tx = ClockDomain('gth_tx')
        platform.import_submodules_to(self)
        ps = self.zynq_ultra_ps_e_0
        self.comb += self.cd_sys.clk.eq(ps.outputs['pl_clk0'])
        self.specials += AsyncResetSynchronizer(self.cd_sys, ~ps.outputs['pl_resetn0'])
        pads = platform.request('sfp_serial')
        refpads = platform.request('gth_refclk')
        refclk = Signal()
        self.specials += Instance('IBUFDS_GTE4', i_I=refpads.p, i_IB=refpads.n,
                                 i_CEB=0, o_O=refclk)
        powergood, lock, txdone, rxdone, cdr = [Signal() for _ in range(5)]
        txpma, rxpma, txactive, rxactive = [Signal() for _ in range(4)]
        txout, rxout, rxerr = [Signal() for _ in range(3)]
        status = Cat(lock, txdone, rxdone, powergood, cdr, txactive, rxactive,
                     ~platform.request('sfp_absent'), platform.request('sfp_los'),
                     platform.request('sfp_fault'))
        self.submodules.monitor = Monitor(status, rxerr)
        monitor = self.monitor
        self.comb += [platform.request('sfp_select').eq(1),
                     platform.request('sfp_disable').eq(~monitor.tx_enable.storage),
                     platform.request('pl_leds', 0).eq(lock),
                     platform.request('pl_leds', 1).eq(rxdone),
                     platform.request('pl_leds', 2).eq(self.monitor.rx_count.value[26]),
                     platform.request('pl_leds', 3).eq(rxerr)]
        for direction, clock, raw_clock, pma_done, active in [
                ('rx', self.cd_gth_rx, rxout, rxpma, rxactive),
                ('tx', self.cd_gth_tx, txout, txpma, txactive)]:
            args = {'i_gtwiz_userclk_'+direction+'_srcclk_in': raw_clock,
                    'i_gtwiz_userclk_'+direction+'_reset_in': ~pma_done,
                    'o_gtwiz_userclk_'+direction+'_usrclk_out': clock.clk,
                    'o_gtwiz_userclk_'+direction+'_active_out': active}
            self.specials += Instance('gtwizard_ultrascale_v1_7_22_gtwiz_userclk_'+direction,
                p_P_CONTENTS=0, p_P_FREQ_RATIO_SOURCE_TO_USRCLK=1,
                p_P_FREQ_RATIO_USRCLK_TO_USRCLK2=1, **args)
            self.specials += AsyncResetSynchronizer(clock, ~pma_done)
        # Mode changes are made only with monitor.reset asserted.
        txprbs, rxprbs, loopback = Signal(4), Signal(4), Signal(3)
        self.specials += [MultiReg(monitor.tx_prbs.storage, txprbs, odomain='gth_tx'),
                         MultiReg(monitor.prbs.storage, rxprbs, odomain='gth_rx'),
                         MultiReg(monitor.loopback.storage, loopback)]
        self.specials += Instance('drtio_gth',
            i_gtwiz_userclk_tx_reset_in=~txpma,
            i_gtwiz_userclk_tx_active_in=txactive, i_gtwiz_userclk_rx_active_in=rxactive,
            i_gtwiz_reset_clk_freerun_in=self.cd_sys.clk,
            i_gtwiz_reset_all_in=monitor.reset.storage | self.cd_sys.rst,
            i_gtwiz_reset_tx_pll_and_datapath_in=0, i_gtwiz_reset_tx_datapath_in=0,
            i_gtwiz_reset_rx_pll_and_datapath_in=0, i_gtwiz_reset_rx_datapath_in=0,
            o_gtwiz_reset_rx_cdr_stable_out=cdr,
            o_gtwiz_reset_tx_done_out=txdone, o_gtwiz_reset_rx_done_out=rxdone,
            i_gtwiz_userdata_tx_in=0, i_drpclk_in=self.cd_sys.clk,
            i_gthrxn_in=pads.rxn, i_gthrxp_in=pads.rxp, i_gtrefclk0_in=refclk,
            i_loopback_in=loopback, i_rxprbssel_in=rxprbs, i_txprbssel_in=txprbs,
            i_rxusrclk_in=self.cd_gth_rx.clk, i_rxusrclk2_in=self.cd_gth_rx.clk,
            i_txusrclk_in=self.cd_gth_tx.clk, i_txusrclk2_in=self.cd_gth_tx.clk,
            o_cplllock_out=lock, o_gthtxn_out=pads.txn, o_gthtxp_out=pads.txp,
            o_gtpowergood_out=powergood, o_rxoutclk_out=rxout, o_txoutclk_out=txout,
            o_rxpmaresetdone_out=rxpma, o_txpmaresetdone_out=txpma,
            o_rxprbserr_out=rxerr)
        if forward_rx_clock:
            # Genesys rev-C SFP_REC_CLK: A2/A1, bank 66, documented 1.2 V.
            # Gate in RX domain; management remains on independent PS clock.
            from misoc.interconnect.csr import CSRStorage
            monitor.forward_enable = CSRStorage(1, name='forward_enable')
            monitor.forward_bootstrap = CSRStorage(1, name='forward_bootstrap')
            self.clock_domains.cd_forward = ClockDomain('forward')
            self.specials += Instance('BUFGCTRL', p_PRESELECT_I0='FALSE',
                p_PRESELECT_I1='TRUE', i_I0=self.cd_sys.clk,
                i_I1=self.cd_gth_rx.clk, i_CE0=1, i_CE1=1,
                i_S0=monitor.forward_bootstrap.storage,
                i_S1=~monitor.forward_bootstrap.storage,
                i_IGNORE0=0, i_IGNORE1=0, o_O=self.cd_forward.clk)
            enable = Signal()
            forwarded = Signal()
            self.specials += MultiReg(monitor.forward_enable.storage, enable,
                                      odomain='forward')
            self.specials += Instance('ODDRE1', p_IS_C_INVERTED=0,
                p_IS_D1_INVERTED=0, p_IS_D2_INVERTED=0, p_SRVAL=0,
                i_C=self.cd_forward.clk, i_D1=enable, i_D2=0,
                i_SR=self.cd_sys.rst, o_Q=forwarded)
            recovery = platform.request('sfp_recovered_clock')
            self.specials += Instance('OBUFDS', i_I=forwarded,
                                      o_O=recovery.p, o_OB=recovery.n)
        self.axi = AXIInterface(data_width=32, address_width=40, id_width=16)
        self.submodules.wb2csr = wishbone2csr.WB2CSR(
            bus_wishbone=wishbone.Interface(data_width=32, address_width=40, addressing='word'),
            bus_csr=csr_bus.Interface(data_width=32, address_width=14))
        self.submodules.axi2wb = AXI2Wishbone(self.axi, self.wb2csr.wishbone, base_address=CSR_BASE)
        self.submodules.banks = csr_bus.CSRBankArray(self,
            lambda name, memory: 0 if name == 'monitor' and memory is None else None,
            data_width=32, address_width=14)
        self.submodules.csr_interconnect = csr_bus.Interconnect(self.wb2csr.csr, self.banks.get_buses())
        connect_ps_hpm0(self, ps, self.axi)

    def write_map(self, path):
        regs = {}
        for name, csrs, bankid, bank in self.banks.banks:
            address = CSR_BASE + bankid * 0x800
            for csr in csrs:
                words = (csr.size + 31) // 32
                regs[name+'_'+csr.name] = {'address': address, 'words': words, 'bits': csr.size}
                address += words * 4
        path.write_text(json.dumps({'kind': 'diagnostic-map-not-hardware-evidence',
            'magic': 0x44525430, 'boot_hz': 125000000, 'registers': regs,
            'status_bits': {'cpll_lock':0, 'tx_done':1, 'rx_done':2, 'powergood':3,
                'cdr_estimate':4, 'tx_active':5, 'rx_active':6, 'module_present':7,
                'rx_los':8, 'tx_fault':9}}, indent=2)+'\n')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--ps', type=Path, required=True)
    p.add_argument('--phy', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument("--forward-rx-clock", action="store_true")
    args = p.parse_args()
    platform = DiagnosticPlatform(args.ps.resolve())
    platform.add_extension([
        ('sfp_serial', 0, Subsignal('txp', Pins('N4')), Subsignal('txn', Pins('N3')),
         Subsignal('rxp', Pins('P2')), Subsignal('rxn', Pins('P1'))),
        ('gth_refclk', 0, Subsignal('p', Pins('Y6')), Subsignal('n', Pins('Y5'))),
        ('sfp_select', 0, Pins('D10'), IOStandard('LVCMOS18')),
        ('sfp_disable', 0, Pins('AB13'), IOStandard('LVCMOS33')),
        ('sfp_absent', 0, Pins('AD14'), IOStandard('LVCMOS33')),
        ('sfp_los', 0, Pins('W14'), IOStandard('LVCMOS33')),
        ('sfp_fault', 0, Pins('AA13'), IOStandard('LVCMOS33')),
    ])
    ip = args.phy.resolve() / 'project/drtio_phy.srcs/sources_1/ip/drtio_gth/drtio_gth.xci'
    platform.add_ip(str(ip))
    # Helpers are installed with the IP, but external helper instances need
    # these sources in the top-level file set as well.
    hdl = args.phy.resolve() / 'project/drtio_phy.gen/sources_1/ip/drtio_gth/hdl'
    for d in ('rx', 'tx'):
        platform.add_source(str(hdl / ('gtwizard_ultrascale_v1_7_gtwiz_userclk_'+d+'.v')))
    config = dict(line.split('=', 1) for line in
                  (args.phy / 'configuration.txt').read_text().splitlines())
    reference_mhz = float(config['CONFIG.RX_REFCLK_FREQUENCY'])
    if reference_mhz not in (125, 156.25) or config['CONFIG.GT_TYPE'] != 'GTH':
        raise ValueError('Unsupported PHY/reference configuration')
    if args.forward_rx_clock:
        platform.add_extension([('sfp_recovered_clock', 0,
            Subsignal('p', Pins('A2')), Subsignal('n', Pins('A1')),
            IOStandard('DIFF_HSTL_I_DCI_12'))])
        platform.add_platform_command('set_property SLEW FAST [get_ports {{sfp_recovered_clock_*}}]')
        platform.add_platform_command('set_property OUTPUT_IMPEDANCE RDRV_48_48 [get_ports {{sfp_recovered_clock_*}}]')
    top = Diagnostic(platform, args.forward_rx_clock)
    platform.add_period_constraint(platform.lookup_request('gth_refclk').p, 1000/reference_mhz)
    first_stage_count = 118 if args.forward_rx_clock else 117
    platform.toolchain.post_synthesis_commands.append("""
# Vivado retains mr_ff on registers; Piotr's old Migen targets nets.
set first_sync [get_cells -hierarchical -filter {mr_ff == TRUE && REF_NAME =~ FD*}]
if {[llength $first_sync] != CDC_COUNT} {error "Missing first-stage CDC registers"}
set_false_path -to [get_pins -of_objects $first_sync -filter {REF_PIN_NAME == D}]
foreach prefix {diagnostic_rx_count_gth_rx diagnostic_tx_count_gth_tx diagnostic_error_count_gth_rx} {
 set sources [get_cells -hierarchical -filter "NAME =~ ${prefix}_gray_source_reg* && REF_NAME =~ FD*"]
 if {[llength $sources] != 32} {write_checkpoint -force gray-debug.dcp; error "Missing Gray source registers: $prefix count=[llength $sources] cells=$sources"}
 set endpoints [all_fanout -flat -endpoints_only -from [get_pins -of_objects $sources -filter {REF_PIN_NAME == Q}]]
 if {[llength $endpoints] != 32} {error "Unexpected Gray CDC endpoints: $prefix"}
 set_bus_skew 8 -from $sources -to $endpoints
}
""".replace("CDC_COUNT", str(first_stage_count)).replace("{", "{{").replace("}", "}}"))
    platform.toolchain.additional_commands.append('report_bus_skew -file top_bus_skew.rpt')
    platform.build(top, build_dir=str(args.output.resolve()), run=False)
    top.write_map(args.output.resolve() / 'csr-map.json')


if __name__ == '__main__':
    main()
