#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Read-only worker command inventory; does not authorize or send commands."""
import argparse,collections,hashlib,json,re
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
repo=Path(__file__).resolve().parents[3]
c=repo/'boards/genesys_zu-5ev/2_firmware_a53/c/kernel_lwip.c'
rust=repo/'boards/genesys_zu-5ev/3_kernel/src/lib.rs'
recovery=repo/'boards/genesys_zu-5ev/3_kernel/src/kernel.rs'
text=c.read_text();calls=[]
for match in re.finditer(r'command\(([0-9]+),([^)]*)\)',text):
 calls.append({'operation':int(match[1]),'line':text[:match.start()].count('\n')+1,'expression':match[0]})
assert collections.Counter(x['operation'] for x in calls)=={1:1,2:1,3:1,4:1,5:2,6:1,7:1},'Worker dispatch sites changed: review required'
for needle in ['if command() != 3','if cmd != 4','if cmd == 7','1 => {','2 => {']:
 assert needle in rust.read_text(),needle
assert 'if crate::command() != 6' in recovery.read_text()
classes={1:('NEW_WORK','ELF load','Reserve worker before command; refuse while master pending/active/held/fault'),2:('NEW_WORK','kernel run','Reserve worker before command; refuse while master pending/active/held/fault'),3:('EXISTING_WORK_PROGRESS','async RPC acknowledgement','Only current worker ticket/epoch and expected RPC event; allow during draining'),4:('EXISTING_WORK_PROGRESS','synchronous RPC reply','Only current worker ticket/epoch and expected RPC reply; allow during draining'),7:('EXISTING_WORK_PROGRESS','RPC exception reply','Only current worker ticket/epoch and expected RPC exception; allow during draining'),5:('ABANDON_UNKNOWN','connection loss/abort','Not quiescence or stop acknowledgement; preserve owner and fault until external reconciliation'),6:('EXISTING_WORK_RECOVERY','uncaught exception recovery','Only current worker exception/recovery phase; preserve ownership until separately qualified fresh READY/quiescence')}
r={'status':'OFFLINE_WORKER_DISPATCH_CLASSIFICATION_COMPLETE_NO_RUNTIME_HOOKS','hardware_admitted':False,'runtime_admitted':False,'source_sha256':{str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in [c,rust,recovery]},'call_sites':calls,'policy':[dict(operation=n,category=x[0],purpose=x[1],obligation=x[2]) for n,x in sorted(classes.items())],'decisions':['Do not blindly interlock all command() calls: blocking RPC completion during draining can deadlock worker retirement','New-work admission and existing-work progress need distinct policy checks, both validated against current ticket/epoch','No automatic grant on busy=0, RPC reply, cancel command5, exception command6, loaded status or stale READY event','Command5 does not imply preemption of running CPU1; command6 is exception-phase protocol, not general reset/stop','Keep cache/mailbox publication unchanged until complete dispatch-path integration reviewed'],'limits':['Source classification only; no command guard implemented or task quiescence proved','Existing gate models new dispatch only; progress/recovery classifier and phase evidence still required','Target ownership-composition build remains separate queued job'],'next_safe_offline':'Prototype command-class policy with same-ticket RPC progress allowed during draining, new work denied, and cancellation/recovery unable to fabricate quiescence'}
a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,indent=2)+'\n');print(r['status'],len(calls),'call sites')
