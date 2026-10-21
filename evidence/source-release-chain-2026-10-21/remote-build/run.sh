#!/bin/bash
set -u
cd /srv/nvme-fast-1/vivado-work/artiq-source-build-20261021 || exit 2
printf 'WAITING_FOR_BUILD_LOCK\n' > state.txt
exec 9>/srv/nvme-fast-1/vivado-work/.vivado-build.lock
flock 9 || exit 3
printf 'RUNNING\n' > state.txt
/home/codex-hil/.local/bin/vivado -mode batch -nojournal -log vivado.log -source top.tcl > console.log 2>&1
result=$?
printf '{"returncode":%d}\n' "$result" > exit.json
if [ "$result" = 0 ]; then printf 'FINISHED_CHECK_REPORTS\n' > state.txt; else printf 'FAILED\n' > state.txt; fi
exit "$result"
