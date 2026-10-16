/* C layout for upstream Rust DDMA codec ABI; LGPL-3.0-or-later. */
#pragma once
#include <stdint.h>
#include <stddef.h>
struct ddma_packet {
 uint32_t source,destination,id,status,length,succeeded,error,channel;
 uint64_t timestamp;
 uint8_t trace[1010];
};
_Static_assert(offsetof(struct ddma_packet,timestamp)==32,"DDMA timestamp ABI");
_Static_assert(offsetof(struct ddma_packet,trace)==40,"DDMA trace ABI");
_Static_assert(sizeof(struct ddma_packet)==1056,"DDMA packet ABI");
int32_t aux_ddma_decode(const uint8_t *,uintptr_t,struct ddma_packet *);
int32_t aux_ddma_encode(uint32_t,const struct ddma_packet *,uint8_t *,uintptr_t);
