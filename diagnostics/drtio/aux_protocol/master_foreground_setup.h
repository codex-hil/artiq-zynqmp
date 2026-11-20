/* SPDX-License-Identifier: LGPL-3.0-or-later */
#pragma once
#include "master_foreground_owner.h"
#include "master_setup_cooperative.h"
/* Offline composition ONLY. No mailbox, MMIO binding or production hooks.
 * Admission and physical ownership receipts remain external. Single caller,
 * no recursive step/open. Each backend must check ownership before external
 * accesses; cancellation cannot interrupt a callback already executing.
 */
struct mfs_session {struct msc_setup setup;struct mfo_gate *gate;uint64_t ticket,epoch;unsigned initialized;};
static inline int mfs_authorized(const struct mfs_session *s){
 return s&&s->initialized&&s->gate&&s->gate->state==MFO_MASTER&&
  s->gate->owner==MFO_MASTER_OWNER&&s->ticket==s->gate->ticket&&s->epoch==s->gate->epoch;
}
static inline int mfs_open(struct mfs_session *s,struct mfo_gate *g,uint64_t ticket,uint32_t action_budget,uint32_t route_budget){
 if(!s||!g||!ticket||g->ticket!=ticket||g->state!=MFO_MASTER||g->owner!=MFO_MASTER_OWNER)return MFO_INVALID;
 if(g->setup_ticket==ticket)return MFO_BUSY;
 struct mfs_session candidate={.gate=g,.ticket=ticket,.epoch=g->epoch,.initialized=1};
 int r=msc_init_epoch(&candidate.setup,action_budget,route_budget,1);if(r)return r;
 g->setup_ticket=ticket;*s=candidate;return 0; /* Open once for grant; never use to replay same grant. */
}
static inline int mfs_step(struct mfs_session *s,const struct msc_io *io){
 if(!s||!s->initialized||!s->gate)return MFO_INVALID;
 struct mfo_gate *g=s->gate;
 if(g->ticket!=s->ticket||g->epoch!=s->epoch||g->owner!=MFO_MASTER_OWNER){msc_cancel(&s->setup);return MFO_INVALID;}
 if(g->state==MFO_FAULT){msc_cancel(&s->setup);return g->error;}
 if(g->state==MFO_HELD&&s->setup.plan.action==MS_COMPLETE)return 1;
 if(!mfs_authorized(s)){msc_cancel(&s->setup);return MFO_BUSY;}
 int r=msc_step(&s->setup,io);
 /* A synchronous backend revocation wins, without faulting a new owner. */
 if(!mfs_authorized(s)){
  msc_cancel(&s->setup);
  return g->ticket==s->ticket&&g->epoch==s->epoch&&g->state==MFO_FAULT?g->error:MFO_INVALID;
 }
 int fault=mfo_setup_result(g,s->ticket,r);return fault?fault:r;
}
static inline int mfs_cancel(struct mfs_session *s){
 if(!s||!s->initialized||!s->gate)return MFO_INVALID;
 msc_cancel(&s->setup);
 if(s->ticket!=s->gate->ticket||s->epoch!=s->gate->epoch||s->gate->owner!=MFO_MASTER_OWNER)return MFO_INVALID;
 return mfo_fault(s->gate,MFO_CANCELLED);
}
