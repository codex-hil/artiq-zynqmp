#!/usr/bin/env bash
# SPDX-License-Identifier: LGPL-3.0-or-later
set -euo pipefail
arm_tool=/srv/nvme-fast-2/toolchains/arm-gnu/arm-gnu-toolchain-13.2.Rel1-x86_64-aarch64-none-elf/bin/aarch64-none-elf
"${arm_tool}-ld" -r master_route_compile.o --start-group libgenesys_aux_codec.a --end-group -o master_route_linked.o
"${arm_tool}-readelf" -h master_route_linked.o > linked-header.txt
"${arm_tool}-nm" -u master_route_linked.o > linked-undefined.txt
"${arm_tool}-nm" --defined-only master_route_linked.o > linked-defined.txt
"${arm_tool}-objdump" -dr master_route_linked.o > linked-disassembly.txt
sha256sum master_route_compile.o libgenesys_aux_codec.a master_route_linked.o > linked-hashes.txt
! grep -E ' U aux_master_leaf_encode$| U aux_master_routing_ack_decode$' linked-undefined.txt
grep -E ' T aux_master_leaf_encode$' linked-defined.txt
grep -E ' T aux_master_routing_ack_decode$' linked-defined.txt
echo MASTER_ROUTE_A53_GENUINE_RUST_RELOCATABLE_LINK_PASS_NOT_EXECUTABLE
