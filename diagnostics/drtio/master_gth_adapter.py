# SPDX-License-Identifier: LGPL-3.0-or-later
"""Isolated adapter for the existing drtio_gth raw20 wizard profile.

Derived wiring pattern from diag_gateware.py. Caller owns independent125MHz
freerun/DRP clock and reset request. The pinned IP reference is156.25MHz;
that is separate from125MHz freerun. Native derived clock qualification is pending. No platform pins/IP sources/constraints are
installed by this module. Userclk active is not an independent clock watchdog.
"""
from types import SimpleNamespace
from migen import Module,Signal,ClockDomain,ClockDomainsRenamer,Instance
from migen.genlib.resetsync import AsyncResetSynchronizer
from protocol_probe import WordAligner

class MasterGTHAdapter(Module):
    def __init__(self,pads,refpads,freerun_clock,reset_request,tx_raw):
        if len(tx_raw)!=20:
            raise ValueError('Existing GTH profile requires raw20 TX')
        self.control_clock=freerun_clock
        self.tx_clock=Signal();self.rx_clock=Signal()
        self.rx_raw=Signal(20)
        refclk=Signal();unshifted=Signal(20)
        self.rx_unaligned=unshifted
        lock,powergood,cdr,txdone,rxdone,txpma,rxpma,txactive,rxactive=[Signal() for _ in range(9)]
        txout,rxout,rxerr=[Signal() for _ in range(3)]
        self.raw_status=SimpleNamespace(lock=lock,powergood=powergood,cdr=cdr,
            txdone=txdone,rxdone=rxdone,txpma=txpma,rxpma=rxpma,
            txactive=txactive,rxactive=rxactive,rxerr=rxerr)
        self.specials+=Instance('IBUFDS_GTE4',i_I=refpads.p,i_IB=refpads.n,i_CEB=0,o_O=refclk)
        for direction,raw,pma,clock,active in (
                ('tx',txout,txpma,self.tx_clock,txactive),
                ('rx',rxout,rxpma,self.rx_clock,rxactive)):
            args={f'i_gtwiz_userclk_{direction}_srcclk_in':raw,
                  f'i_gtwiz_userclk_{direction}_reset_in':~pma,
                  f'o_gtwiz_userclk_{direction}_usrclk_out':clock,
                  f'o_gtwiz_userclk_{direction}_active_out':active}
            self.specials+=Instance('gtwizard_ultrascale_v1_7_22_gtwiz_userclk_'+direction,
                p_P_CONTENTS=0,p_P_FREQ_RATIO_SOURCE_TO_USRCLK=1,
                p_P_FREQ_RATIO_USRCLK_TO_USRCLK2=1,**args)
        self.clock_domains.cd_gt_align=ClockDomain('gt_align')
        self.comb+=self.cd_gt_align.clk.eq(self.rx_clock)
        self.specials+=AsyncResetSynchronizer(self.cd_gt_align,
            reset_request | ~rxpma | ~rxdone | ~rxactive)
        self.submodules.aligner=ClockDomainsRenamer('gt_align')(WordAligner())
        self.comb += [self.aligner.input.eq(unshifted),self.rx_raw.eq(self.aligner.output)]
        self.link_status=SimpleNamespace(reset_done=rxdone,clock_active=rxactive,
                                         aligned=self.aligner.aligned)
        self.specials+=Instance('drtio_gth',
            i_gtwiz_userclk_tx_reset_in=~txpma,
            i_gtwiz_userclk_tx_active_in=txactive,i_gtwiz_userclk_rx_active_in=rxactive,
            i_gtwiz_reset_clk_freerun_in=freerun_clock,i_drpclk_in=freerun_clock,
            i_gtwiz_reset_all_in=reset_request,
            i_gtwiz_reset_tx_pll_and_datapath_in=0,i_gtwiz_reset_tx_datapath_in=0,
            i_gtwiz_reset_rx_pll_and_datapath_in=0,i_gtwiz_reset_rx_datapath_in=0,
            o_gtwiz_reset_rx_cdr_stable_out=cdr,
            o_gtwiz_reset_tx_done_out=txdone,o_gtwiz_reset_rx_done_out=rxdone,
            i_gtwiz_userdata_tx_in=tx_raw,o_gtwiz_userdata_rx_out=unshifted,
            i_gthrxn_in=pads.rxn,i_gthrxp_in=pads.rxp,i_gtrefclk0_in=refclk,
            i_loopback_in=0,i_rxprbssel_in=0,i_txprbssel_in=0,
            i_rxusrclk_in=self.rx_clock,i_rxusrclk2_in=self.rx_clock,
            i_txusrclk_in=self.tx_clock,i_txusrclk2_in=self.tx_clock,
            o_cplllock_out=lock,o_gthtxn_out=pads.txn,o_gthtxp_out=pads.txp,
            o_gtpowergood_out=powergood,o_rxoutclk_out=rxout,o_txoutclk_out=txout,
            o_rxpmaresetdone_out=rxpma,o_txpmaresetdone_out=txpma,o_rxprbserr_out=rxerr)
