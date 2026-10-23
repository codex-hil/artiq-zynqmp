#!/usr/bin/env bash
# SPDX-License-Identifier: LGPL-3.0-or-later
set -euo pipefail
[[ $# == 1 && ! -e "$1" ]] || { echo 'Require fresh output directory' >&2; exit 2; }
repo=$(cd "$(dirname "$0")/.." && pwd)
output=$(realpath -m "$1")
mkdir -p "$output"
clang=/srv/codex-hil-data/artiq-zynqmp/toolchains/abi-verified/bin/clang-irrt
linker=/srv/codex-hil-data/artiq-zynqmp/toolchains/abi-verified/root/usr/lib/llvm-19/bin/ld.lld
source_dir="$repo/diagnostics/ddr/bounded_test"
for source in pattern.c ocm_model.c entry.S; do
 "$clang" --target=aarch64-none-elf -ffreestanding -fno-builtin -fno-stack-protector -mgeneral-regs-only -O2 -Wall -Wextra -Werror -c "$source_dir/$source" -o "$output/$source.o"
done
"$linker" -T "$source_dir/link.ld" "$output/entry.S.o" "$output/pattern.c.o" "$output/ocm_model.c.o" -o "$output/model.elf"
nm -n "$output/model.elf" > "$output/symbols.txt"
readelf -lW "$output/model.elf" > "$output/layout.txt"
python3 "$repo/scripts/check_ocm_image.py" --elf "$output/model.elf" --symbols "$output/symbols.txt" --output "$output/check.json"
