#!/usr/bin/env python3
"""Preprocess AMD diagnostic PMU options without building/loading firmware; LGPL-3.0-or-later."""
import argparse,hashlib,json,re,subprocess
from pathlib import Path
CC=Path('/srv/codex-hil-data/toolchains/amd/Xilinx/2025.2/Vivado/gnu/microblaze/lin/bin/mb-gcc')
PROFILES={'baseline':{},'pm_disabled':{'ENABLE_PM_VAL':0},'service_reduced':{n:0 for n in ['ENABLE_PM_VAL','ENABLE_SCHEDULER_VAL','ENABLE_FPGA_LOAD_VAL','ENABLE_FPGA_READ_CONFIG_REG_VAL','ENABLE_FPGA_READ_CONFIG_DATA_VAL','ENABLE_SECURE_VAL','ENABLE_MEM_RANGE_VAL','ENABLE_SECURE_FLAG_VAL','ENABLE_EM_VAL']}}
def macros(text):
 return {m[1]:m[2] for line in text.splitlines() if (m:=re.fullmatch(r'#define ([A-Za-z_]\w*)\s*(.*)',line))}
def review(build,out):
 if out.exists():raise ValueError('Fresh output required')
 header=build/'pmu-app/src/xpfw_config.h';includes=build/'pmu-bsp/include'
 out.mkdir(parents=True);result={}
 for name,options in PROFILES.items():
  command=[str(CC),'-E','-dM','-x','c','-DSDT','-DPSU_PMU=1U','-I'+str(includes),'-include',str(header)]+['-D'+n+'='+str(v) for n,v in options.items()]+['/dev/null']
  text=subprocess.check_output(command,text=True,stderr=subprocess.STDOUT,timeout=20);(out/(name+'.macros')).write_text(text)
  all_macros=macros(text);enabled=sorted(n for n in all_macros if n.startswith('ENABLE_') and not n.endswith('_VAL') and all_macros[n]=='')
  if name!='baseline' and 'ENABLE_PM' in enabled:raise ValueError('PM disable overridden')
  result[name]={'defines':options,'enabled_service_macros':enabled,'sleep_when_idle':'SLEEP_WHEN_IDLE' in all_macros,'macro_sha256':hashlib.sha256(text.encode()).hexdigest()}
 report={'status':'PMU_OPTION_PREPROCESS_REVIEW_ONLY','hardware_executed':False,'destructive_test_allowed':False,'profiles':result,'compiler_version':subprocess.check_output([str(CC),'--version'],text=True).splitlines()[0],'inputs':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [header,includes/'xparameters.h',includes/'bspconfig.h',build/'pmu-app/build/compile_commands.json']},'limitations':['Actual target preprocessor with SDT/PSU_PMU defines and BSP includes, not linked-image equivalence.','Disabling PM alone leaves other services; even reduced macros do not prove ROM/interrupt/DDR inactivity.','Existing FSBL has conditional XFsbl_PmInit -> XPm_SetConfiguration path; no-PM is not admitted as drop-in replacement.','No PMU firmware built/loaded or PMU stop/event mask/ROM modification performed.'],'decision':'Do not deploy no-PM during existing trained boot. Next evaluate boot-compatible explicit post-handoff quiescence/telemetry with acknowledgments, or dedicated diagnostic boot matching reduced PMU; preserve AMD implementation.'}
 (out/'review.json').write_text(json.dumps(report,indent=2)+'\n');return report
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();print(json.dumps(review(a.build,a.output),indent=2))
