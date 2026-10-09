#!/usr/bin/env python3
"""Attach debug transport to an isolated, already generated CPU0 application."""
import argparse,json,shutil
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--app',type=Path,required=True);p.add_argument('--csr-map',type=Path,required=True)
a=p.parse_args();repo=Path(__file__).resolve().parent.parent;r=json.loads(a.csr_map.read_text())['registers'];src=a.app/'src'
names={'MON_CHAN':'rtio_moninj_mon_chan_sel','MON_SEL':'rtio_moninj_mon_probe_sel','MON_UPDATE':'rtio_moninj_mon_value_update','MON_VALUE':'rtio_moninj_mon_value','MON_INJ_CHAN':'rtio_moninj_inj_chan_sel','MON_INJ_SEL':'rtio_moninj_inj_override_sel','MON_INJ_VALUE':'rtio_moninj_inj_value','AN_ENABLE':'rtio_analyzer_enable','AN_CLEAR':'rtio_analyzer_clear','AN_COUNT':'rtio_analyzer_count','AN_INDEX':'rtio_analyzer_read_index','AN_UPDATE':'rtio_analyzer_read_update','AN_DATA':'rtio_analyzer_data','AN_DEPTH':'rtio_analyzer_depth','AN_OVERFLOW':'rtio_analyzer_encoder_overflow','AN_OVERFLOW_RESET':'rtio_analyzer_encoder_overflow_reset'}
assert r['rtio_analyzer_data']['words']==8 and r['rtio_analyzer_count']['words']==2
(src/'debug_csr.h').write_text(''.join(f'#define {k} 0x{r[v]["address"]:x}UL\n' for k,v in names.items()))
shutil.copyfile(repo/'boards/genesys_zu-5ev/2_firmware_a53/c/debug_lwip.c',src/'debug_lwip.c')
p=src/'main.c';s=p.read_text();assert 'genesys_debug_start' not in s, 'Debug services already attached'
anchor='extern int genesys_kernel_start(void);';assert s.count(anchor)==1
s=s.replace(anchor,anchor+'\nextern int genesys_debug_start(void);')
anchor='    if (genesys_kernel_start())';assert s.count(anchor)==1
s=s.replace(anchor,'    if (genesys_debug_start()) { xil_printf("Debug services unavailable\\r\\n"); return 1; }\n'+anchor);p.write_text(s)
p=src/'CMakeLists.txt';s=p.read_text();anchor='collect (PROJECT_LIB_SOURCES kernel_lwip.c)';assert s.count(anchor)==1;p.write_text(s.replace(anchor,anchor+'\ncollect (PROJECT_LIB_SOURCES debug_lwip.c)'))
