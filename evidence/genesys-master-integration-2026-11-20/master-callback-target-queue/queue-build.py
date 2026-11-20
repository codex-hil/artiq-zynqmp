#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Bounded capacity waiter for this frozen offline job; never touches boards."""
import json,subprocess,time
from pathlib import Path
root=Path(__file__).resolve().parent
report=root/'queued-build-status.json'
def save(status,**extra):
 temporary=report.with_suffix('.tmp')
 temporary.write_text(json.dumps(dict(status=status,hardware_admitted=False,**extra),indent=2)+'\n')
 temporary.replace(report)
command=['/home/codex-hil/.local/bin/dell-build-slot','--','bash','-c','set -e; sha256sum --check input-sha256.txt; bash build-cooperative-setup-emulation.sh']
for attempt in range(1,91):
 save('WAITING_FOR_SHARED_DELL_SLOT',attempt=attempt,max_attempts=90)
 r=subprocess.run(command,cwd=root,capture_output=True,text=True)
 (root/f'queued-attempt-{attempt:03d}.log').write_text(r.stdout+r.stderr)
 if r.returncode==75 and 'Build capacity busy (three slots or legacy exclusive job).' in r.stderr:
  if attempt<90:time.sleep(20)
  continue
 save('BUILD_PASS_EXECUTION_PENDING' if r.returncode==0 else 'BUILD_FAILED_NO_RETRY',attempt=attempt,exit_code=r.returncode)
 raise SystemExit(r.returncode)
save('CAPACITY_WAIT_EXHAUSTED',attempts=90)
raise SystemExit(75)
