#!/usr/bin/env python3
"""Offline PMU wake-route evidence, not exclusion proof; LGPL-3.0-or-later."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

ANCHORS={
 'xpfw_mod_pm.c':['static void PmIpiHandler(', 'XPfw_PmIpiHandler(SrcMask,',
                  'static void PmEventHandler(', 'XPfw_PmWakeHandler(RegValue)',
                  'XPFW_EV_ACPU_1_WAKE','XPFW_EV_R5_0_WAKE'],
 'pm_core.c':['static void PmRequestWakeup(', 'PmMasterCanRequestWake(',
              'status = PmMasterWakeProc(proc);','case PM_API(PM_REQUEST_WAKEUP):'],
 'pm_master.c':['s32 PmMasterWakeProc(', 'PmProcFsm(proc, PM_PROC_EVENT_WAKE)',
                's32 PmWakeMasterBySlave(', 'status = PmMasterWake(mst);'],
 'pm_proc.c':['static s32 PmProcWake(', 'status = proc->wake();',
              'case PM_PROC_EVENT_WAKE:', 'return (s32)XpbrACPU1WakeHandler();'],
 'xpfw_config.h':['#define SLEEP_WHEN_IDLE','#define ENABLE_PM']}


def source_record(path,anchors):
    data=path.read_bytes();lines=data.decode().splitlines()
    hits={a:[i for i,line in enumerate(lines,1) if a in line] for a in anchors}
    if not all(hits.values()):raise ValueError('Missing required route anchor '+str(path))
    return dict(path=str(path.resolve()),sha256=hashlib.sha256(data).hexdigest(),anchors=hits)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    elf=a.build/'build/zynqmp_pmufw.elf'
    raw=subprocess.run(['nm',str(elf)],check=True,capture_output=True,text=True,timeout=20).stdout
    names={line.split()[-1] for line in raw.splitlines() if line.split()}
    required={'PmIpiHandler','PmProcFsm','PmProcWake','PmMasterWake'}
    if not required<=names:raise ValueError('Missing linked wake-route symbols')
    result=dict(status='OFFLINE_PMU_WAKE_AUTHORITY_PRESENT',hardware_executed=False,
                elf=dict(path=str(elf.resolve()),sha256=hashlib.sha256(elf.read_bytes()).hexdigest()),
                linked_required_symbols=sorted(required),
                sources=[source_record(a.build/'src'/n,anchors) for n,anchors in ANCHORS.items()],
                destructive_test_allowed=False,
                limits='Routes and symbols establish capability, not executed event history, current permissions/masks or a source-to-binary equivalence proof. SLEEP_WHEN_IDLE is not disabled PM service.')
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
