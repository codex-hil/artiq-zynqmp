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
xvlog vendor/*.v tb_cpll_drp_sequence.v /srv/codex-hil-data/toolchains/amd/Xilinx/2025.2/Vivado/data/verilog/src/glbl.v
xelab -mt off -L unisims_ver tb_cpll_drp_sequence glbl -s cal_sequence
for delay in 2 5; do
 xsim cal_sequence -testplusarg "DRP_DELAY=$delay" -runall > "simulation-$delay.log" 2>&1
 cat "simulation-$delay.log"
 ! grep -E "Fatal:|Error:" "simulation-$delay.log"
 grep -F "CPLL_DRP_SEQUENCE_PASS" "simulation-$delay.log"
done
'
