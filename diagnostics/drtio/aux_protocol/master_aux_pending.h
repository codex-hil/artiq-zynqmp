/* SPDX-License-Identifier: LGPL-3.0-or-later */
#pragma once
#include "master_aux_resumable_tx.h"
#include "master_aux_resumable_rx.h"
/* Offline asynchronous one-request driver, NOT legacy mr_io callback ABI.
 * Sole owner across all steps; target/profile/clock/epoch/packet capability
 * qualification external. No request IDs: delayed/duplicate valid ACKs remain
 * uncorrelated. Never reset/reopen a consumed request to retry unknown outcome.
 * One TX OR RX step/turn, max1buscallback; decoder step may panic/hang externally.
 */
enum map_phase {MAP_TX,MAP_RX,MAP_DONE,MAP_FAILED};
enum map_error {MAP_INVALID=-20,MAP_UNEXPECTED=-21,MAP_CANCELLED=-22};
struct map_request {struct mm_transport *mm;struct mat_session tx;struct mar_session rx;ma_fixed_decoder decode;unsigned started;enum map_phase phase;uint32_t expected,kind;int terminal;};
static inline int map_fail(struct map_request *s,int error){
 if(!s)return MAP_INVALID;
 if(!s->terminal){s->terminal=error<0?error:MAP_INVALID;s->phase=MAP_FAILED;if(s->mm)mm_fail(s->mm);}
 return s->terminal;
}
static inline int map_begin(struct map_request *s,struct mm_transport *m,const uint8_t *bytes,size_t size,ma_fixed_decoder decode,uint32_t expected,unsigned reviewed_epoch){
 if(!s||s->started||!decode||!expected)return MAP_INVALID;
 /* Preserve packet aliases inside tx.bytes; never zero TX before copying. */
 int r=mat_begin(&s->tx,m,bytes,size,reviewed_epoch);if(r)return r;
 s->mm=m;s->decode=decode;s->started=1;s->phase=MAP_TX;s->expected=expected;
 s->kind=0;s->terminal=0;s->rx=(struct mar_session){0};return 0;
}
static inline void map_cancel(struct map_request *s){
 if(!s||!s->started||s->terminal)return;
 enum map_phase phase=s->phase;map_fail(s,MAP_CANCELLED);
 if(phase==MAP_TX)mat_cancel(&s->tx);else if(phase==MAP_RX)mar_cancel(&s->rx);
}
static inline int map_step(struct map_request *s){
 if(!s||!s->started)return MAP_INVALID;
 if(s->terminal)return s->terminal;
 if(s->phase==MAP_TX){
  int r=mat_step(&s->tx);if(s->terminal)return s->terminal;
  if(r<0)return map_fail(s,r);
  if(r==1){int opened=mar_begin(&s->rx,s->mm,s->decode,1);if(opened)return map_fail(s,opened);s->phase=MAP_RX;}
  return 0; /* Never execute RX IO in same turn as TX completion. */
 }
 if(s->phase==MAP_RX){
  int r=mar_step(&s->rx);if(s->terminal)return s->terminal;
  if(r<0)return map_fail(s,r);
  if(r==1){if(s->rx.kind!=s->expected)return map_fail(s,MAP_UNEXPECTED);s->kind=s->rx.kind;s->phase=MAP_DONE;s->terminal=1;return 1;}
  return 0;
 }
 return map_fail(s,MAP_INVALID);
}
