/* SPDX-License-Identifier: LGPL-3.0-or-later */
#pragma once
#include "master_route_setup.h"
/* Canonical one-link star candidate. Fresh/drained exclusive epoch externally
 * qualified; io must retain pre-send queue checks/CRC-checked replies. 257 ACKs
 * are transport acceptance only, not satellite routing capability/readback.
 */
struct mst_table {struct mt_transaction tx;unsigned consumed,completed,send_attempts;};
static inline void mst_init_epoch(struct mst_table *s){
 if(s){mt_init_new_epoch(&s->tx);s->consumed=0;s->completed=0;s->send_attempts=0;}
}
static inline int mst_run_once(struct mst_table *s,const struct mr_io *io,uint32_t budget){
 if(!s||!io||!io->send||!io->recv||!budget||budget>4096)return MT_INVALID;
 if(s->consumed)return MT_BUSY;
 s->consumed=1;
 for(unsigned stage=0;stage<257;stage++){
  if(stage&&mt_next_after_success(&s->tx))return MT_INVALID;
  uint8_t bytes[40];int n=stage<256?aux_master_star_path_encode(stage,bytes,sizeof(bytes)):aux_master_leaf_encode(0x31,1,bytes,sizeof(bytes));
  if(n<=0){s->tx.state=MT_FAILED;s->tx.result=MT_INVALID;return MT_INVALID;}
  int r=mt_begin(&s->tx,stage<256?0x30:0x31,budget);if(r)return r;
  s->send_attempts++;
  r=mt_tx_complete(&s->tx,io->send(io->ctx,bytes,(size_t)n)==0);if(r)return r;
  while(s->tx.state==MT_WAIT){uint32_t kind=0;int packet=io->recv(io->ctx,&kind);r=mt_poll(&s->tx,packet,kind);if(r)return r;}
  s->completed++;
 }
 return MT_OK;
}
