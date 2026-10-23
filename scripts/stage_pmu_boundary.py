#!/usr/bin/env python3
"""Stage AMD PMU loop telemetry in a fresh copy; no firmware load. LGPL-3.0-or-later."""
import argparse,hashlib,json,shutil
from pathlib import Path
REPO=Path(__file__).resolve().parents[1]
INCLUDE='#include "xpfw_core.h"\n'
LOOP='\t\tdo {\n\n\t\t#ifdef SLEEP_WHEN_IDLE'
def transform(text):
 if text.count(INCLUDE)!=1 or text.count(LOOP)!=1 or 'ARTIQ_PMU_BOUNDARY_TELEMETRY' in text:raise ValueError('Unexpected AMD loop source')
 text=text.replace(INCLUDE,INCLUDE+'#ifdef ARTIQ_PMU_BOUNDARY_TELEMETRY\n#include "artiq_pmu_boundary.h"\n#endif\n')
 return text.replace(LOOP,'\t\tdo {\n#ifdef ARTIQ_PMU_BOUNDARY_TELEMETRY\n            artiq_pmu_observe_boundary();\n#endif\n\n\t\t#ifdef SLEEP_WHEN_IDLE')
def stage(build,out):
 if out.exists():raise ValueError('Fresh output required')
 original=build/'pmu-app/src';out.mkdir(parents=True);shutil.copytree(original,out/'src',symlinks=True)
 before=(original/'xpfw_core.c').read_text();(out/'src/xpfw_core.c').write_text(transform(before))
 header=REPO/'diagnostics/ddr/pmu_boundary/telemetry.h';shutil.copyfile(header,out/'src/artiq_pmu_boundary.h')
 sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 if sha(original/'xpfw_core.c')!=hashlib.sha256(before.encode()).hexdigest():raise ValueError('Original changed during staging')
 report={'status':'ISOLATED_SOURCE_STAGED_NOT_FIRMWARE','hardware_executed':False,'destructive_test_allowed':False,'original_sha256':sha(original/'xpfw_core.c'),'patched_sha256':sha(out/'src/xpfw_core.c'),'telemetry_sha256':sha(header),'compile_define':'ARTIQ_PMU_BOUNDARY_TELEMETRY=1','limits':'Observation-only loop boundary. No request transport, ACK, interrupt mask, PMU park, ROM exclusion or DDR ownership. No linked firmware artifact.'}
 (out/'stage.json').write_text(json.dumps(report,indent=2)+'\n');return report
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();print(json.dumps(stage(a.build,a.output),indent=2))
