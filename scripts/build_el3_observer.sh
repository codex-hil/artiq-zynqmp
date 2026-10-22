#!/usr/bin/env bash
# SPDX-License-Identifier: LGPL-3.0-or-later
set -euo pipefail
if [ "$#" -ne 2 ]; then echo 'Usage: build_el3_observer.sh TOOL_PREFIX FRESH_OUTPUT' >&2; exit 2; fi
prefix=$1
output=$2
repo=$(cd -- "$(dirname -- "$0")/.." && pwd)
if [ -e "$output" ]; then echo 'Use fresh output' >&2; exit 2; fi
mkdir -p "$output"
"${prefix}gcc" -nostdlib -nostartfiles -static -Wl,--build-id=none -Wl,--fatal-warnings \
 -Wl,-T,"$repo/diagnostics/ddr/el3_observer/link.ld" \
 "$repo/diagnostics/ddr/el3_observer/entry.S" -o "$output/observer.elf"
"${prefix}objdump" -d "$output/observer.elf" > "$output/disassembly.txt"
"${prefix}readelf" -lWs "$output/observer.elf" > "$output/layout.txt"
