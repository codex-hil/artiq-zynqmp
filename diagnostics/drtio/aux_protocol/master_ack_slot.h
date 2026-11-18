/* SPDX-License-Identifier: LGPL-3.0-or-later */
#pragma once
#include "master_leaf_codec.h"
/* Host-only fixed-slot adapter. acquire:0 empty,1 exclusive stable borrowed
 * slot+ticket until release,other error with no ownership transferred.
 * Owned slots must be1024bytes. release consumes ticket exactly once, even if
 * it reports failure: outcome unknown, never retry. Callbacks bounded by caller.
 * CRC validates first8byte RoutingAck envelope; remaining slot bytes are stale
 * storage, NOT additional frame bytes. No real MMIO/ring/epoch proof here.
 */
struct ma_slot_io {void *ctx;
 int (*acquire)(void *,const uint8_t **,size_t *,uint32_t *);
 int (*release)(void *,uint32_t);};
struct ma_slot_state {unsigned poisoned;};
/* Return1 decoded/released ACK,0 empty,-1 error. Acquisition/decode/release errors poison state;
 * invalid arguments return without callbacks or state changes. No further callback until external qualified recovery/new state object.
 * kind is changed only on success AFTER release succeeded.
 */
static inline int ma_receive(struct ma_slot_state *s,const struct ma_slot_io *io,uint32_t *kind) {
 if(!s||!io||!io->acquire||!io->release||!kind)return -1;
 if(s->poisoned)return -1;
 const uint8_t *slot=0;size_t size=0;uint32_t ticket=0;
 int acquired=io->acquire(io->ctx,&slot,&size,&ticket);
 if(acquired==0)return 0;
 if(acquired!=1){s->poisoned=1;return -1;}
 int decoded=-4;
 if(slot&&size==1024)decoded=aux_master_routing_ack_decode(slot,8);
 int released=io->release(io->ctx,ticket);
 if(decoded!=0x32||released){s->poisoned=1;return -1;}
 *kind=0x32;return 1;
}
