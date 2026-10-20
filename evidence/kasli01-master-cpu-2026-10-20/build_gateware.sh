#!/usr/bin/env bash
set -euo pipefail
out=/srv/codex-hil-data/artiq-zynqmp/build/kasli01-dma-start-result-2026-10-20
build="$out/generated/genesys_drtio_master_v11"
python_bin=/srv/codex-hil-data/artiq-zynqmp/venv/bin/python
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
# Upstream suppresses .bit and emits only .bin; retain both promised artifacts.
bit=p.with_name('top_bitstream.tcl')
bit.write_text(bit.read_text().replace(' -no_binary_bitfile', ''))
PY
cd "$build/gateware"
"${VIVADO:-/home/codex-hil/.local/bin/vivado}" -mode batch -source top.tcl > build.log 2>&1
if ! grep -q 'All user specified timing constraints are met.' top_timing.rpt; then
  echo 'Kasli timing did not close; inspect reports' >&2; exit 1
fi
for artifact in top.bit top.bin ../software/bootloader/bootloader.bin; do test -s "$artifact"; done
sha256sum top.bit top.bin ../software/bootloader/bootloader.bin > "$out/artifacts.sha256"
