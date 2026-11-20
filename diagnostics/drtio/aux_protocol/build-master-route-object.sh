#!/usr/bin/env bash
# SPDX-License-Identifier: LGPL-3.0-or-later
# Dell unique job directory; no firmware/runtime or hardware access.
set -euo pipefail
arm_tool=/srv/nvme-fast-2/toolchains/arm-gnu/arm-gnu-toolchain-13.2.Rel1-x86_64-aarch64-none-elf/bin/aarch64-none-elf
"${arm_tool}-gcc" --version > compiler.txt
"${arm_tool}-gcc" -mcpu=cortex-a53 -O2 -std=c11 -Wall -Wextra -Werror -ffreestanding -fno-builtin -fno-stack-protector -c master_route_compile.c -o master_route_compile.o
"${arm_tool}-readelf" -h master_route_compile.o > object-header.txt
"${arm_tool}-nm" -u master_route_compile.o > undefined.txt
"${arm_tool}-nm" --defined-only master_route_compile.o > defined.txt
"${arm_tool}-objdump" -dr master_route_compile.o > disassembly.txt
sha256sum *.h *.c build-master-route-object.sh master_route_compile.o > hashes.txt
echo MASTER_ROUTE_A53_C_OBJECT_COMPILE_PASS_NOT_LINKED
