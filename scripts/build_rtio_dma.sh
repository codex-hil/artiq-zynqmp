#!/usr/bin/env bash
# Build Piotr PS integration + upstream RTIO DMA in a separate output tree.
set -euo pipefail
if [ "$#" -ne 1 ]; then echo "Usage: $0 FRESH_OUTPUT_DIRECTORY" >&2; exit 2; fi
repo=$(cd -- "$(dirname -- "$0")/.." && pwd)
out=$(realpath -m "$1")
if [ -e "$out" ]; then echo "Use a fresh output directory" >&2; exit 2; fi
mkdir -p "$out"
cd "$out"
vivado -mode batch -source "$repo/boards/genesys_zu-5ev/0_platform/vivado_script.tcl" -tclargs local-rtio-dma > platform-build.log 2>&1
export PYTHONPATH="$repo/common/artiq:$repo/common/migen${PYTHONPATH:+:$PYTHONPATH}"
"${PYTHON:-/srv/codex-hil-data/artiq-zynqmp/venv/bin/python}" "$repo/boards/genesys_zu-5ev/1_gateware/gateware.py" \
    -B . -M migen-build --variant local-rtio-dma --no-run > gateware-generate.log 2>&1
cd migen-build
printf '%s\n' 'set_param general.maxThreads 2' 'source top.tcl' > top_limited.tcl
vivado -mode batch -source top_limited.tcl > build.log 2>&1
sha256sum ../platform.xsa csr-map.json top.v top.bit > artifacts.sha256
