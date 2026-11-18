/* SPDX-License-Identifier: LGPL-3.0-or-later */
#pragma once
#include "master_leaf_codec.h"
#include "master_transaction.h"
/* Isolated fixed-leaf host candidate. Initialize ONCE per externally qualified
 * fresh/drained link epoch. Exclusive owner; no concurrent/unsolicited traffic.
 * Callbacks must return in bounded time. recv returns0 none,1 CRC-checked packet,
 * other error. No physical clock/transport/epoch qualification is provided here.
 */
struct mr_io {void *ctx;int (*send)(void *,const uint8_t *,size_t);
 int (*recv)(void *,uint32_t *);};
struct mr_setup {struct mt_transaction tx[2];unsigned consumed,completed;};
static inline void mr_init_epoch(struct mr_setup *s) {
 if(s){mt_init_new_epoch(&s->tx[0]);mt_init_new_epoch(&s->tx[1]);s->consumed=0;s->completed=0;}
}
static inline int mr_run_once(struct mr_setup *s,const struct mr_io *io,uint32_t budget) {
 if(!s||!io||!io->send||!io->recv||!budget||budget>4096)return MT_INVALID;
 if(s->consumed)return MT_BUSY;
 s->consumed=1;
 for(unsigned stage=0;stage<2;stage++) {
  uint8_t bytes[40];uint32_t request=0x30+stage;
  int n=aux_master_leaf_encode(request,1,bytes,sizeof(bytes));
  if(n<=0){s->tx[stage].state=MT_FAILED;s->tx[stage].result=MT_INVALID;return MT_INVALID;}
  int r=mt_begin(&s->tx[stage],request,budget);if(r)return r;
  r=mt_tx_complete(&s->tx[stage],io->send(io->ctx,bytes,(size_t)n)==0);
  if(r)return r;
  while(s->tx[stage].state==MT_WAIT) {
   uint32_t kind=0;int packet=io->recv(io->ctx,&kind);
   r=mt_poll(&s->tx[stage],packet,kind);if(r)return r;
  }
  s->completed++;
 }
 return MT_OK;
}
