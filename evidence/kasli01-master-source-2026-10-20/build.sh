#!/usr/bin/env bash
set -euo pipefail
export ARTIQ_SOURCE=/srv/codex-hil-data/artiq-zynqmp/work/kasli01-bram-runtime-dma-start-result
export PYTHONPATH="$ARTIQ_SOURCE:/srv/codex-hil-data/artiq-zynqmp/reference/migen:/srv/codex-hil-data/artiq-zynqmp/work/kasli-misoc:/srv/codex-hil-data/artiq-zynqmp/venvs/artiq-host/lib/python3.12/site-packages"
export CARGO_HOME=/srv/codex-hil-data/artiq-zynqmp/build/kasli-v1.1-master-2026-10-13/cargo-home
/srv/codex-hil-data/artiq-zynqmp/venv/bin/python -m artiq.gateware.targets.kasli /srv/codex-hil-data/artiq-zynqmp/build/kasli01-dma-start-result-2026-10-20/config.json --integrated-rom-size 131072 --output-dir /srv/codex-hil-data/artiq-zynqmp/build/kasli01-dma-start-result-2026-10-20/generated --no-compile-gateware
