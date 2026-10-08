#!/usr/bin/env bash
set -euo pipefail
if [ "$#" -ne 1 ]; then echo "Usage: $0 OUTPUT_DIRECTORY" >&2; exit 2; fi
repo=$(cd "$(dirname "$0")/../.." && pwd)
out=$(realpath -m "$1")
export ARTIQ_SOURCE=${ARTIQ_SOURCE:-/srv/codex-hil-data/artiq-zynqmp/work/kasli-master}
export MIGEN_SOURCE=${MIGEN_SOURCE:-/srv/codex-hil-data/artiq-zynqmp/reference/migen}
export MISOC_SOURCE=${MISOC_SOURCE:-/srv/codex-hil-data/artiq-zynqmp/work/kasli-misoc}
python_bin=${PYTHON:-/srv/codex-hil-data/artiq-zynqmp/venv/bin/python}
host_site=${ARTIQ_HOST_SITE:-/srv/codex-hil-data/artiq-zynqmp/venvs/artiq-host/lib/python3.12/site-packages}
export PYTHONPATH="$ARTIQ_SOURCE:$MIGEN_SOURCE:$MISOC_SOURCE:$host_site${PYTHONPATH:+:$PYTHONPATH}"
export PATH="$(dirname "$python_bin"):$PATH"
export CARGO_HOME=${CARGO_HOME:-$out/cargo-home}
mkdir -p "$out"
"$python_bin" -m artiq.gateware.targets.kasli \
  "$repo/diagnostics/kasli-master/kasli-v2.1-master.json" \
  --output-dir "$out/generated" --no-compile-gateware > "$out/firmware-generate.log" 2>&1
build="$out/generated/genesys_drtio_master"
"$python_bin" - "$build/gateware/top_route.tcl" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1]);s=p.read_text()
# Keep shared Migen unchanged; Vivado 2025.2 retains mr_ff on registers.
fix='''
set first_sync [get_cells -hierarchical -filter {mr_ff == TRUE && REF_NAME =~ FD*}]
if {[llength $first_sync] == 0} {error "Missing Migen CDC first-stage registers"}
set_false_path -to [get_pins -of_objects $first_sync -filter {REF_PIN_NAME == D}]
'''
lines=s.splitlines();i=next(i for i,l in enumerate(lines) if l.startswith('synth_design '))
lines.insert(i+1,fix)
p.write_text('set_param general.maxThreads 2\n'+'\n'.join(lines)+'\n')
PY
cd "$build/gateware"
"${VIVADO:-/home/codex-hil/.local/bin/vivado}" -mode batch -source top.tcl > build.log 2>&1
if ! grep -q 'All user specified timing constraints are met.' top_timing.rpt; then
  echo 'Kasli timing did not close; inspect reports' >&2; exit 1
fi
for artifact in top.bit top.bin ../software/bootloader/bootloader.bin ../software/runtime/runtime.elf ../software/runtime/runtime.fbi; do
  test -s "$artifact"
done
sha256sum top.bit top.bin ../software/bootloader/bootloader.bin ../software/runtime/runtime.elf ../software/runtime/runtime.fbi > "$out/artifacts.sha256"
