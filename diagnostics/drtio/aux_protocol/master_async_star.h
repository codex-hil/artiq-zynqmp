/* SPDX-License-Identifier: LGPL-3.0-or-later */
#pragma once
#include "master_aux_pending.h"
/* Offline canonical256path+rank sender. One request pending at a time, one
 * TX/RX step per turn; preparation-only turns perform no bus callback.
 * Total budget includes preparation/decode turns, not elapsed time.
 * Exclusive owner/fresh epoch and actual satellite table-apply capability are
 * external obligations; ACKkind alone cannot prove apply or reject stale ACK.
 */
enum mas_error {MAS_INVALID=-30,MAS_BUDGET=-31,MAS_CANCELLED=-32};
struct mas_table {struct mm_transport *mm;struct map_request request;uint32_t left;unsigned started,completed,requests_started;int terminal;};
static inline int mas_fail(struct mas_table *s,int error){
 if(!s)return MAS_INVALID;
 if(!s->terminal){s->terminal=error<0?error:MAS_INVALID;map_cancel(&s->request);if(s->mm)mm_fail(s->mm);}
 return s->terminal;
}
static inline int mas_begin(struct mas_table *s,struct mm_transport *m,uint32_t total_turns,unsigned reviewed_epoch){
 if(!s||s->started||!mm_ready(m)||m->held||!total_turns||total_turns>10000000||reviewed_epoch!=1)return MAS_INVALID;
 *s=(struct mas_table){.mm=m,.left=total_turns,.started=1};return 0;
}
static inline void mas_cancel(struct mas_table *s){if(s&&s->started&&!s->terminal)mas_fail(s,MAS_CANCELLED);}
static inline int mas_step(struct mas_table *s){
 if(!s||!s->started)return MAS_INVALID;
 if(s->terminal)return s->terminal;
 if(!s->left)return mas_fail(s,MAS_BUDGET);
 s->left--;
 if(!s->request.started){
  if(s->completed>=257)return mas_fail(s,MAS_INVALID);
  uint8_t bytes[40];unsigned stage=s->completed;
  int n=stage<256?aux_master_star_path_encode(stage,bytes,sizeof(bytes)):aux_master_leaf_encode(0x31,1,bytes,sizeof(bytes));
  if(n<=0)return mas_fail(s,MAS_INVALID);
  int r=map_begin(&s->request,s->mm,bytes,(size_t)n,aux_master_routing_ack_decode,0x32,1);
  if(r)return mas_fail(s,r);
  s->requests_started++; /* Encoded/armed, not a claimed hardware commit. */
 }else{
  int r=map_step(&s->request);if(s->terminal)return s->terminal;
  if(r<0)return mas_fail(s,r);
  if(r==1){
   s->completed++;
   if(s->completed==257){s->terminal=1;return 1;} /* Accept last budget unit. */
   s->request=(struct map_request){0}; /* DISTINCT next request after ACK+pop. */
  }
 }
 return s->left?0:mas_fail(s,MAS_BUDGET);
}
