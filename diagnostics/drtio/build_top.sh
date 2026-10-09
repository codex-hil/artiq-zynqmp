#!/usr/bin/env bash
set -euo pipefail
if [ "$#" -ne 3 ]; then echo "Usage: $0 PS_EXPORT PHY_EXPORT FRESH_OUTPUT" >&2; exit 2; fi
repo=$(cd "$(dirname "$0")/../.." && pwd)
ps=$(realpath "$1")
phy=$(realpath "$2")
out=$(realpath -m "$3")
if [ -e "$out" ]; then echo 'Use a fresh output directory' >&2; exit 2; fi
mkdir -p "$out"
export PYTHONPATH="${ARTIQ_SOURCE:-$repo/common/artiq}:$repo/common/migen:${MISOC_SOURCE:-/srv/codex-hil-data/artiq-zynqmp/reference/misoc-current}${PYTHONPATH:+:$PYTHONPATH}"
python_bin=${PYTHON:-/srv/codex-hil-data/artiq-zynqmp/venv/bin/python}
extra=()
if [ "${FORWARD_RX_CLOCK:-0}" = 1 ]; then extra+=(--forward-rx-clock); fi
if [ "${DRTIO_PROTOCOL:-0}" = 1 ]; then extra+=(--protocol); fi
"$python_bin" "$repo/diagnostics/drtio/diag_gateware.py" "${extra[@]}" --ps "$ps" --phy "$phy" --output "$out" > "$out/generate.log" 2>&1
# Piotr's Migen importer emits synth_ip in project mode. Use proper IP runs
# without modifying the archived Migen checkout.
"$python_bin" - "$out" <<'PY'
from pathlib import Path
import sys
out=Path(sys.argv[1])
s=(out/'top_route.tcl').read_text()
for name in ('drtio_gth','platform_zynq_ultra_ps_e_0_0'):
 old=f'synth_ip [get_ips {name}] -force'
 new=f'''create_ip_run [get_ips {name}]
launch_runs {name}_synth_1 -jobs 2
wait_on_run {name}_synth_1
if {{[get_property PROGRESS [get_runs {name}_synth_1]] ne "100%"}} {{error "IP synthesis failed: {name}"}}'''
 if old not in s:raise RuntimeError('Unexpected Migen IP invocation: '+name)
 s=s.replace(old,new)
(out/'top_route.tcl').write_text('set_param general.maxThreads 2\n'+s)
PY
cd "$out"
vivado -mode batch -source top.tcl > build.log 2>&1
sha256sum top.bit top.v top.xdc csr-map.json > artifacts.sha256
"$python_bin" "$repo/diagnostics/drtio/check_top_build.py" "$out" --output "$out/results.json"
