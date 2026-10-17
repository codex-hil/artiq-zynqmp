#!/usr/bin/env bash
set -euo pipefail
export ARTIQ_SOURCE=/srv/codex-hil-data/artiq-zynqmp/work/kasli03-bram-runtime-dma-result
export PYTHONPATH="$ARTIQ_SOURCE:/srv/codex-hil-data/artiq-zynqmp/reference/migen:/srv/codex-hil-data/artiq-zynqmp/work/kasli-misoc:/srv/codex-hil-data/artiq-zynqmp/venvs/artiq-host/lib/python3.12/site-packages"
export CARGO_HOME=/srv/codex-hil-data/artiq-zynqmp/build/kasli-v1.1-master-2026-10-13/cargo-home
/srv/codex-hil-data/artiq-zynqmp/venv/bin/python -m artiq.gateware.targets.kasli /srv/codex-hil-data/artiq-zynqmp/build/kasli03-bram-netboot-2026-10-13/config.json --integrated-rom-size 131072 --output-dir /srv/codex-hil-data/artiq-zynqmp/build/kasli03-dma-result-2026-10-17/generated --no-compile-gateware
