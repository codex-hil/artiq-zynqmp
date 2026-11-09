#!/usr/bin/env bash
set -euo pipefail
arm_tool=/srv/nvme-fast-2/toolchains/arm-gnu/arm-gnu-toolchain-13.2.Rel1-x86_64-aarch64-none-elf/bin/aarch64-none-elf
"${arm_tool}-gcc" --version | head -1
"${arm_tool}-gcc" -mcpu=cortex-a53 -O2 -std=c11 -Wall -Wextra -Werror -ffreestanding -fno-builtin -fno-stack-protector -c reset_compile.c -o reset_compile.o
"${arm_tool}-readelf" -h reset_compile.o > object-header.txt
"${arm_tool}-nm" -u reset_compile.o > undefined.txt
test ! -s undefined.txt
"${arm_tool}-objdump" -dr reset_compile.o > disassembly.txt
sha256sum reset_compile.c reset_driver.h shape_recovery.h master_driver.h master_regs.h reset_compile.o > hashes.txt
echo RESET_A53_OBJECT_COMPILE_PASS
