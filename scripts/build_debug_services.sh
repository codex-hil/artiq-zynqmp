#!/usr/bin/env bash
# Reuse the existing two-core services build, then attach standard debug ports.
set -euo pipefail
if [ "$#" -ne 4 ]; then echo 'Usage: SYSTEM_TOP_DTS DEBUG_CSR_MAP FRESH_OUTPUT ARM_GNU_PREFIX' >&2; exit 2; fi
repo=$(cd "$(dirname "$0")/.." && pwd)
sdt=$(realpath "$1");csr=$(realpath "$2");out=$(realpath -m "$3");arm=$(realpath "$4")
bash "$repo/scripts/build_a53_services.sh" "$sdt" "$csr" "$out" "$arm" --kernel
python3 "$repo/scripts/attach_rtio_debug.py" --app "$out/amd/app" --csr-map "$csr"
vivado-container shell -c '
set -eu
amd=${AMD_ROOT:-/srv/codex-hil-data/toolchains/amd/Xilinx/2025.2}
export PATH="$1/bin:$amd/tps/lnx64/cmake-3.24.2/bin:$PATH"
exec "$amd/Vivado/bin/empyro" build_app -w "$2"
' build "$arm" "$out/amd/app"
sha256sum "$sdt" "$csr" "$repo/boards/genesys_zu-5ev/2_firmware_a53/c/debug_lwip.c" "$out/amd/app/build/lwip_echo_server.elf" > "$out/debug-artifacts.sha256"
