/* SPDX-License-Identifier: LGPL-3.0-or-later */
#pragma once
#include <stdint.h>
#include <stddef.h>
/* Isolated candidate, not currently linked into A53 firmware.
 * kind0x30/value1: destination1, hops[0]=1/rest0 (40 bytes).
 * kind0x31/value1: rank1 (8 bytes). No other topology accepted.
 * Returns length or -2 unsupported kind/value, -4 null/bad capacity,
 * -3 upstream serialization error. Invalid arguments do not write output.
 * Buffer must be valid/writable for capacity bytes; ownership is caller's.
 */
int32_t aux_master_leaf_encode(uint32_t kind,uint32_t value,uint8_t *buffer,size_t capacity);
/* Exact8-byte RoutingAck envelope; returns0x32, -4 null/length, -1 CRC,
 * -2 wrong kind, -3 upstream decode error. No transaction correlation. */
int32_t aux_master_routing_ack_decode(const uint8_t *buffer,size_t length);
/* Canonical upstream default_master(1) path: destination0 [0,ff..],
 * destination1 [1,0,ff..], destination2..255 [ff..]. Requires all256 entries
 * before rank1 to replace unknown/stale peer table; this call sends nothing.
 * Capacity40..1024, destination0..255. -4 null/capacity,-2 destination,-3 codec.
 */
int32_t aux_master_star_path_encode(uint32_t destination,uint8_t *buffer,size_t capacity);
