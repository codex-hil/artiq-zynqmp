#!/usr/bin/env bash
# Run inside vivado-container shell, reusing the SDT from build_boot_firmware.sh.
set -euo pipefail
if [ "$#" -ne 3 ]; then
    echo "Usage: $0 SYSTEM_TOP_DTS OUTPUT ARM_GNU_PREFIX" >&2
    exit 2
fi
repo=$(cd -- "$(dirname -- "$0")/.." && pwd)
sdt=$(realpath "$1")
output=$(realpath -m "$2")
arm=$(realpath "$3")
amd=${AMD_ROOT:-/srv/codex-hil-data/toolchains/amd/Xilinx/2025.2}
export PATH="$arm/bin:$amd/tps/lnx64/cmake-3.24.2/bin:$PATH"
mkdir -p "$output"
cd "$output"
esw="$amd/Vivado/bin/empyro"
"$esw" repo -st "$amd/Vivado/data/embeddedsw"
"$esw" create_bsp -w "$output/bsp" -s "$sdt" -p psu_cortexa53_0 -t lwip_echo_server -r "$output/.repo.yaml"
"$esw" create_app -d "$output/bsp" -t lwip_echo_server -w "$output/app" -r "$output/.repo.yaml"
python3 "$repo/scripts/patch_ethernet_sources.py" --app "$output/app" --bsp "$output/bsp"
"$esw" build_app -w "$output/app"
sha256sum "$sdt" "$output/app/build/lwip_echo_server.elf" > "$output/artifacts.sha256"
