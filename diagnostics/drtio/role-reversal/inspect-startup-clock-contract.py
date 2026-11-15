#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Bounded source guards for startup clock-mode review; not frequency proof."""
import argparse,ast,json,re,hashlib
from pathlib import Path
def inspect(adapter,cal,power,tx,rx):
 tree=ast.parse(adapter)
 helpers=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='Instance' and any(k.arg=='p_P_FREQ_RATIO_SOURCE_TO_USRCLK' for k in n.keywords)]
 assert len(helpers)==1
 args={k.arg:ast.literal_eval(k.value) for k in helpers[0].keywords if k.arg and k.arg.startswith('p_')}
 assert args['p_P_CONTENTS']==0 and args['p_P_FREQ_RATIO_SOURCE_TO_USRCLK']==args['p_P_FREQ_RATIO_USRCLK_TO_USRCLK2']==1
 for helper,direction in ((tx,'tx'),(rx,'rx')):
  assert re.search(r'\.CE\s*\(1\x27b1\)',helper)
  assert re.search(r'\.CLR\s*\(gtwiz_userclk_'+direction+r'_reset_in\)',helper)
  assert re.search(r'\.DIV\s*\(P_USRCLK_DIV\)',helper)
 assert re.search(r'MOD_TXOUTCLK_SEL\s*=\s*3\x27b101',cal)
 assert re.search(r'GTHE4_TXOUTCLKSEL_OUT\s*<=\s*txoutclksel_int',cal)
 assert re.search(r'GT_RXRATE\s*=\s*pwr_on_fsm\s*\?\s*USER_RXRATE\s*:\s*3\x27b001',power)
 assert "i_gtwiz_userclk_tx_reset_in=~txpma" in adapter
 assert "f'i_gtwiz_userclk_{direction}_reset_in':~pma" in adapter
 return args
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('ip',type=Path);p.add_argument('adapter',type=Path);a=p.parse_args()
 paths=[a.adapter]+[a.ip/'hdl'/n for n in ('gtwizard_ultrascale_v1_7_gthe4_cpll_cal_tx.v','gtwizard_ultrascale_v1_7_gthe4_delay_powergood.v','gtwizard_ultrascale_v1_7_gtwiz_userclk_tx.v','gtwizard_ultrascale_v1_7_gtwiz_userclk_rx.v')]
 texts=[f.read_text() for f in paths];args=inspect(*texts)
 bad=list(texts);bad[0]=bad[0].replace('p_P_FREQ_RATIO_SOURCE_TO_USRCLK=1','p_P_FREQ_RATIO_SOURCE_TO_USRCLK=2')
 try:inspect(*bad)
 except AssertionError:pass
 else:raise AssertionError('Changed divider accepted')
 print(json.dumps({'status':'SOURCE_STARTUP_CLOCK_CONTRACT_GUARDS_PASS_DIVIDER_MUTANT_REFUSED','helper_params':args,'mode_findings':['CPLL calibration TX selector override101, otherwise synchronized user selector','Non-PCIe power-good branch RXRATE001 before done; USER_RXRATE after done','External TX/RX userclk BUFG_GT CE1 DIV0 (ratio1), CLR from inverse respective PMAresetdone'],'open_contracts':['Need exact generated parent branch binding and PMAresetdone/selector handover timeline; source guards alone do not prove simultaneous behavior','CSR may advance at physical-link-not-ready and stats have withdrawal tail; cannot infer Gray quiescence from admit/link readiness','No qualified fastest active producer period during startup/calibration; no numeric skew/max-delay bound authorized by this review'],'next':'Diagnostic finite mode matrix for actual pinned GT primitive with TX selectors000/101/010 and RXRATE001/000; derive clocks without manual periods, then review which modes can coexist with active producer clocks','limits':['Source syntax/parameter guards not formal FSM or physical GT timing proof','No XDC/default changes, hardware access or adoption'],'source_sha256':{str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in paths}},indent=2))
