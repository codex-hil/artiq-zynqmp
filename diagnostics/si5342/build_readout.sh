#!/usr/bin/env bash
set -euo pipefail
out=$(realpath -m "${1:?Specify output directory}")
repo=$(cd "$(dirname "$0")/../.." && pwd)
bsp=/srv/codex-hil-data/artiq-zynqmp/build-vivado/ethernet-reproduced/bsp
arm=/srv/codex-hil-data/artiq-zynqmp/toolchains/arm-gnu/arm-gnu-toolchain-13.2.Rel1-x86_64-aarch64-none-elf
linker=/srv/codex-hil-data/artiq-zynqmp/build-vivado/ethernet-reproduced/app/src/lscript.ld
mkdir -p "$out"
source_name=${SI_SOURCE:-readout}
case "$source_name" in readout|control) ;; *) exit 2 ;; esac
"$arm/bin/aarch64-none-elf-gcc" -DSDT -specs="$bsp/Xilinx.spec" -I"$bsp/include" -Wall -Wextra -O2 -g \
 "$repo/diagnostics/si5342/$source_name.c" -Wl,-T,"$linker" -L"$bsp/lib" \
 -Wl,--start-group -lxilstandalone -lxiltimer -lxil -lgcc -lc -Wl,--end-group -o "$out/si5342-$source_name.elf"
sha256sum "$out/si5342-$source_name.elf" "$repo/diagnostics/si5342/$source_name.c" > "$out/$source_name.sha256"
