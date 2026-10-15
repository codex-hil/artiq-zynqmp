/* Actual-load acknowledgement gate, LGPL-3.0-or-later.
 * Count zero denotes reset/uninitialized; wrap is not supported in this lab.
 * A gap/fault blocks ACKs until a new observed reset epoch. */
#pragma once
#include <stdint.h>
struct tsc_ack_state { uint32_t seen, blocked; };
static inline int tsc_ack_step(struct tsc_ack_state *s, uint32_t count,
                              int reset, int ready, int fault) {
 if(reset) {s->seen=0;s->blocked=0;return 0;}
 if(!ready)return 0;
 if(fault) {
  if(s->blocked)return 0;
  s->blocked=1;return -1;
 }
 if(s->blocked)return 0;
 if(count==0) {s->seen=0;return 0;}
 if(count==s->seen)return 0;
 if(count!=s->seen+1) {s->blocked=1;return -1;}
 s->seen=count;
 return 1;
}
