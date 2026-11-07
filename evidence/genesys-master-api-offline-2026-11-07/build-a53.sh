#!/bin/bash
set -euo pipefail
job=$(cd "$(dirname "$0")" && pwd)
tool=/srv/nvme-fast-2/toolchains/arm-gnu/arm-gnu-toolchain-13.2.Rel1-x86_64-aarch64-none-elf/bin/aarch64-none-elf
cd "$job"
sha256sum source/master_a53.c source/master_driver.h source/master_regs.h > inputs.sha256
"$tool-gcc" --version > compiler-version.txt
"$tool-gcc" -std=c11 -mcpu=cortex-a53 -O2 -Wall -Wextra -Werror -ffreestanding -fno-builtin -fno-stack-protector -Isource -c source/master_a53.c -o master_a53.o
"$tool-objdump" -dr master_a53.o > master_a53.dis
"$tool-readelf" -h master_a53.o > elf-header.txt
"$tool-nm" -u master_a53.o > undefined-symbols.txt
test ! -s undefined-symbols.txt
grep -q 'AArch64' elf-header.txt
grep -q 'dsb' master_a53.dis
sha256sum -c inputs.sha256 > source-check.txt
sha256sum master_a53.o > object.sha256
printf 'A53_COMPILE_ONLY_PASS_NO_HARDWARE\n' > status.txt
