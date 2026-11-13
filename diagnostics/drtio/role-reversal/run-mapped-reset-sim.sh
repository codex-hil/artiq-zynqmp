#!/usr/bin/env bash
# SPDX-License-Identifier: LGPL-3.0-or-later
# Run on Dell inside the unique job directory with reset_five_domains.v and the bench.
set -euo pipefail
image=localhost/pm12-xsim-runtime:20261104
expected=b7b066512d328abaf5dce280d01973e1a64c85fa46602426d015df17f36d2155
actual=$(podman image inspect "$image" --format '{{.Id}}')
[[ "$actual" == "$expected" ]] || { echo 'Simulator image identity changed'; exit 1; }
exec /home/codex-hil/.local/bin/dell-build-slot -- podman run --rm --init --network=none \
 --mount type=bind,src=/srv/codex-hil-data/toolchains/amd/Xilinx,dst=/srv/codex-hil-data/toolchains/amd/Xilinx,ro=true \
 --mount "type=bind,src=$PWD,dst=$PWD" --workdir "$PWD" "$image" bash -c '
set -euo pipefail
source /srv/codex-hil-data/toolchains/amd/Xilinx/2025.2/Vivado/settings64.sh
command -v gcc
gcc --version | head -n 1
xvlog mapped_reset.v tb_mapped_reset.v /srv/codex-hil-data/toolchains/amd/Xilinx/2025.2/Vivado/data/verilog/src/glbl.v
for top in tb_mapped_reset tb_mapped_ce_bad tb_mapped_and_bad tb_mapped_handover_bad tb_mapped_set_bad; do
 xelab -mt off -L unisims_ver "$top" glbl -s "$top"
 xsim "$top" -runall > "$top.log" 2>&1
 cat "$top.log"
 if [[ "$top" == tb_mapped_reset ]]; then
  ! grep -E "Fatal:|Error:" "$top.log"
  grep -F "MAPPED_RESET_SLICE_PASS" "$top.log"
 else
  grep -F "Fatal:" "$top.log"
  ! grep -F "MAPPED_RESET_SLICE_PASS" "$top.log"
  if [[ "$top" == tb_mapped_handover_bad ]]; then
   grep -F "MAPPED_INITIAL_RELEASE_PASS" "$top.log"
   grep -F "coordinator releases after fresh PL edges" "$top.log"
  fi
  if [[ "$top" == tb_mapped_set_bad ]]; then
   grep -F "MAPPED_INITIAL_RELEASE_PASS" "$top.log"
   grep -F "mapped coordinator owns reset at control release" "$top.log"
  fi
 fi
done
'
