/* SPDX-License-Identifier: LGPL-3.0-or-later */
#pragma once
#include "master_route_setup.h"
/* Separate host-only incremental candidate; does not replace blocking sender.
 * One send OR one recv callback maximum per step. A callback can still perform
 * many MMIO operations or hang: caller latency/recovery qualification required.
 * Return0 pending,1 candidate transport complete,negative terminal failure.
 * Budget counts receive callbacks, not elapsed time or scheduling fairness.
 */
struct msi_table {struct mt_transaction tx;unsigned initialized,completed,send_attempts;uint32_t budget;int terminal;};
static inline int msi_init_epoch(struct msi_table *s,uint32_t budget,int reviewed_epoch){
 if(!s||!budget||budget>4096||reviewed_epoch!=1)return MT_INVALID;
 *s=(struct msi_table){.initialized=1,.budget=budget};mt_init_new_epoch(&s->tx);return MT_OK;
}
static inline int msi_fail(struct msi_table *s,int error){s->terminal=error<0?error:MT_INVALID;return s->terminal;}
static inline int msi_step(struct msi_table *s,const struct mr_io *io){
 if(!s||!s->initialized||!io||!io->send||!io->recv)return MT_INVALID;
 if(s->terminal)return s->terminal;
 if(s->tx.state==MT_DONE&&mt_next_after_success(&s->tx))return msi_fail(s,MT_INVALID);
 if(s->tx.state==MT_IDLE){
  unsigned stage=s->completed;uint8_t bytes[40];
  if(stage>=257)return msi_fail(s,MT_INVALID);
  int n=stage<256?aux_master_star_path_encode(stage,bytes,sizeof(bytes)):aux_master_leaf_encode(0x31,1,bytes,sizeof(bytes));
  if(n<=0)return msi_fail(s,MT_INVALID);
  int r=mt_begin(&s->tx,stage<256?0x30:0x31,s->budget);if(r)return msi_fail(s,r);
  s->send_attempts++;
  int sent=io->send(io->ctx,bytes,(size_t)n);
  if(s->terminal)return s->terminal;
  r=mt_tx_complete(&s->tx,sent==0);
  return r?msi_fail(s,r):0;
 }
 if(s->tx.state==MT_WAIT){
  uint32_t kind=0;int packet=io->recv(io->ctx,&kind);
  if(s->terminal)return s->terminal;
  int r=mt_poll(&s->tx,packet,kind);
  if(r)return msi_fail(s,r);
  if(s->tx.state==MT_DONE&&++s->completed==257){s->terminal=1;return 1;}
  return 0;
 }
 return msi_fail(s,MT_INVALID);
}
static inline void msi_cancel(struct msi_table *s){if(s&&s->initialized&&s->terminal>=0)msi_fail(s,MT_IO);}
