#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Pin generated calibration intent; source guards are not DRP proof."""
import argparse,json,re,hashlib
from pathlib import Path
def inspect(top,wrapper,cal,generated):
 def number(name):
  m=re.search(r'\.'+name+r'\((\d+(?:\.\d+)?)\)',top);assert m,name;return float(m[1])
 params={n:number(n) for n in ('C_CPLL_VCO_FREQUENCY','C_FREERUN_FREQUENCY','C_PCIE_ENABLE','C_SIM_CPLL_CAL_BYPASS')}
 assert params=={'C_CPLL_VCO_FREQUENCY':2500.0,'C_FREERUN_FREQUENCY':125.0,'C_PCIE_ENABLE':0.0,'C_SIM_CPLL_CAL_BYPASS':1.0}
 assert re.search(r'GTHE4_CHANNEL_TX_PROGDIV_CFG\s*\(0\.0\)',wrapper)
 assert re.search(r'MOD_PROGDIV_CFG\s*=\s*16\x27hE062;\s*//divider 20',cal)
 assert re.search(r'MOD_TXOUTCLK_SEL\s*=\s*3\x27b101',cal)
 assert "ADDR_TX_PROGDIV_CFG = 10'h03E" in cal
 assert re.search(r'di_msk\s*<=\s*MOD_PROGDIV_CFG',cal)
 assert 'progdiv_cfg_store' in cal and 'RESTORE_PROGDIV' in cal
 assert '(C_CPLL_VCO_FREQUENCY/20)' in generated
 return params
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('ip',type=Path);a=p.parse_args()
 files=[a.ip/'synth/drtio_gth.v',a.ip/'synth/drtio_gth_gthe4_channel_wrapper.v',a.ip/'hdl/gtwizard_ultrascale_v1_7_gthe4_cpll_cal_tx.v',a.ip/'synth/drtio_gth_gtwizard_gthe4.v'];texts=[f.read_text() for f in files];params=inspect(*texts)
 bad=list(texts);bad[0]=bad[0].replace('.C_CPLL_VCO_FREQUENCY(2500.0)','.C_CPLL_VCO_FREQUENCY(5000.0)')
 try:inspect(*bad)
 except AssertionError:pass
 else:raise AssertionError('Unreviewed VCO accepted')
 print(json.dumps({'status':'PINNED_CALIBRATION_DIVIDER_SOURCE_GUARDS_PASS_VCO_MUTANT_REFUSED','source_sha256':{str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in files},'generated_actual_parameters':params,'static_tx_progdiv_cfg':0,'calibration_intent':{'drp_address_hex':'03E','source_word_hex':'E062','vendor_source_divider_comment':20,'tx_selector':'101','monitor_expected_from_generated_formula_mhz':params['C_CPLL_VCO_FREQUENCY']/20},'findings':['Static timing DCP does not replay firmware-independent vendor DRP state machine writes; selector cases alone leave configured divider0','Calibration source stores/modifies/restores programmable divider; 20 is explicit vendor-source intent, not independent DRP encoding verification','Generated simulation parameter C_SIM_CPLL_CAL_BYPASS1 means generic IP simulation must not be assumed to exercise calibration sequence'],'limits':['No proof actual DRP transaction completes, clock is glitch-free or userclk becomes active only at settled mode','No physical fastest active source bound, numeric CDC constraints or hardware/default changes'],'next':'Compare temporary in-memory TX divider20 snapshot with static divider0, then review DRP/selector/PMA and userclk-clear handover timeline'},indent=2))
