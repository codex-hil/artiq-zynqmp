/* SPDX-License-Identifier: LGPL-3.0-or-later */
#pragma once
#include <stdint.h>
#include <stddef.h>
/* Encode only EchoRequest(kind0,value0) or destination1 status(kind0x20,value1).
 * Both8byte envelopes, valid writable capacity8..1024. Invalid input unchanged.
 * Decode exact8byte EchoReply1,TSCAck4,DestinationDown0x21,DestinationOK0x22.
 * Other replies, ResetAck/routing/variable error payloads intentionally refused.
 * -4 null/length/capacity,-2 unsupported kind/value,-1 CRC,-3 upstream failure.
 * Valid pointer ownership required; no statusUP/TSC/identity/ACK correlation proof.
 */
int32_t aux_master_control_encode(uint32_t,uint32_t,uint8_t *,size_t);
int32_t aux_master_control_decode(const uint8_t *,size_t);
