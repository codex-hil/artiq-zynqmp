#!/usr/bin/env bash
# Run inside vivado-container shell; no Vitis IDE/SDK/PetaLinux required.
set -euo pipefail
if [ "$#" -ne 3 ]; then
    echo "Usage: $0 XSA OUTPUT ARM_GNU_PREFIX" >&2
    exit 2
fi
repo=$(cd -- "$(dirname -- "$0")/.." && pwd)
xsa=$(realpath "$1")
output=$(realpath -m "$2")
arm=$(realpath "$3")
amd=${AMD_ROOT:-/srv/codex-hil-data/toolchains/amd/Xilinx/2025.2}
export PATH="$arm/bin:$amd/tps/lnx64/cmake-3.24.2/bin:$amd/gnu/microblaze/lin/bin:$PATH"
mkdir -p "$output"
cd "$output"
"$amd/Vivado/bin/sdtgen" "$repo/scripts/generate_sdt.tcl" "$xsa" "$output/sdt" "$repo/boards/genesys_zu-5ev/3_bootable/system-user.dtsi"
esw="$amd/Vivado/bin/empyro"
"$esw" repo -st "$amd/Vivado/data/embeddedsw"
"$esw" create_bsp -w "$output/bsp" -s "$output/sdt/system-top.dts" -p psu_cortexa53_0 -t zynqmp_fsbl -r "$output/.repo.yaml"
"$esw" create_app -d "$output/bsp" -t zynqmp_fsbl -w "$output/app" -r "$output/.repo.yaml"
cp "$repo/boards/genesys_zu-5ev/3_bootable/xfsbl_ddr_init.c" "$output/app/src/xfsbl_ddr_init.c"
python3 - "$output/app/src/xfsbl_debug.h" <<'PYTHON'
from pathlib import Path
import sys
p = Path(sys.argv[1])
s = p.read_text()
s = s.replace('#define XFSBL_DEBUG_H', '#define XFSBL_DEBUG_H\n#define FSBL_DEBUG_INFO', 1)
p.write_text(s)
PYTHON
"$esw" build_app -w "$output/app"
"$esw" create_bsp -w "$output/pmu-bsp" -s "$output/sdt/system-top.dts" -p psu_pmu_0 -t zynqmp_pmufw -r "$output/.repo.yaml"
"$esw" create_app -d "$output/pmu-bsp" -t zynqmp_pmufw -w "$output/pmu-app" -r "$output/.repo.yaml"
"$esw" build_app -w "$output/pmu-app"
sha256sum "$xsa" "$output/app/build/zynqmp_fsbl.elf" "$output/pmu-app/build/zynqmp_pmufw.elf" > "$output/artifacts.sha256"
