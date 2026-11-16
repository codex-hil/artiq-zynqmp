# SPDX-License-Identifier: LGPL-3.0-or-later
"""Source-only guards for calibrated lock/reset connectivity, not elaboration proof."""
import argparse, hashlib, json, re
from pathlib import Path

def inspect(generated, wrapper, reset):
    patterns = [
        (generated, r'assign\s+cplllock_int\s*=\s*cplllock_cpll_cal_int\s*;'),
        (generated, r'assign\s+gtwiz_reset_plllock_tx_int\s*=\s*&cplllock_int\s*;'),
        (generated, r'\.plllock_tx_in\s*\(gtwiz_reset_plllock_tx_int\)'),
        (wrapper, r'assign\s+USER_CPLLLOCK_OUT\s*=\s*cal_on_rx_cplllock_out\s*\|\s*cal_on_tx_cplllock_out\s*;'),
        (reset, r'if\s*\(plllock_tx_sync\s*&&\s*\(~sm_reset_tx_timer_clr\)\s*&&\s*sm_reset_tx_timer_sat\)\s*begin\s*gttxreset_out\s*<=\s*1\x27b0;'),
        (reset, r'if\s*\(!plllock_tx_sync\)\s*gtwiz_reset_tx_done_int\s*<=\s*1\x27b0;'),
    ]
    for text, pattern in patterns:
        assert re.search(pattern, text), pattern

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('ip', type=Path); args = ap.parse_args()
    files = [args.ip/'synth/drtio_gth_gtwizard_gthe4.v', args.ip/'hdl/gtwizard_ultrascale_v1_7_gthe4_cpll_cal.v', args.ip/'hdl/gtwizard_ultrascale_v1_7_gtwiz_reset.v']
    texts = [f.read_text() for f in files]; inspect(*texts)
    for index, old, new in [(0, 'assign cplllock_int          = cplllock_cpll_cal_int;', 'assign cplllock_int = cplllock_ch_int;'), (1, 'cal_on_rx_cplllock_out | cal_on_tx_cplllock_out', 'cal_on_tx_cplllock_out'), (2, 'if (!plllock_tx_sync)', 'if (1\'b0)')]:
        assert old in texts[index]
        bad = list(texts); bad[index] = bad[index].replace(old, new)
        try: inspect(*bad)
        except AssertionError: pass
        else: raise AssertionError('Mutant accepted')
    print(json.dumps({'status':'SOURCE_CONNECTIVITY_GUARDS_PASS_THREE_MUTANTS_REFUSED', 'sha256':{str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in files}, 'findings':['Calibration-enabled branch routes wrapper lock to reset helper CPLL input','Wrapper lock is RX-calibration lock OR TX-calibration lock','TX reset helper waits synchronized lock and timer before releasing gttxreset','Lock loss in IDLE clears user reset-done; this source branch does not itself restart reset'], 'limits':['Text guards do not prove elaborated branch selection or joint TX/RX behavior','Previous TX-only test is insufficient to prove wrapper lock masking','TXPMARESETDONE and userclk-clear physical ordering remain open','No hardware, default integration or timing constraints changed'], 'next':'Exercise original TX/RX calibration wrapper with actual PLL selections before connecting reset helper in simulation'}, indent=2))
