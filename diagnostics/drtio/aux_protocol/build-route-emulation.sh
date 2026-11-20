#!/usr/bin/env bash
# SPDX-License-Identifier: LGPL-3.0-or-later
set -euo pipefail
arm_tool=/srv/nvme-fast-2/toolchains/arm-gnu/arm-gnu-toolchain-13.2.Rel1-x86_64-aarch64-none-elf/bin/aarch64-none-elf
for variant in normal panic route-negative; do
 extra=()
 if [[ "$variant" == panic ]]; then extra=(-DFORCE_PANIC); fi
 if [[ "$variant" == route-negative ]]; then extra=(-DFORCE_ROUTE_ASSERT); fi
 "${arm_tool}-gcc" -mcpu=cortex-a53 -O2 -std=c11 -Wall -Wextra -Werror -ffreestanding -fno-builtin -fno-stack-protector -nostdlib -static -Wl,-e,_start -Wl,--build-id=none -DMASTER_A53_EMULATION -DMASTER_ROUTE_EMULATION "${extra[@]}" -include ack-fixture.h master_codec_emulation.c test_master_mmio_route.c libgenesys_aux_codec.a -o "codec-$variant.elf"
 "${arm_tool}-readelf" -h "codec-$variant.elf" > "$variant-header.txt"
 "${arm_tool}-nm" -u "codec-$variant.elf" > "$variant-undefined.txt"
 test ! -s "$variant-undefined.txt"
done
sha256sum *.elf *.h *.c libgenesys_aux_codec.a > emulation-hashes.txt
