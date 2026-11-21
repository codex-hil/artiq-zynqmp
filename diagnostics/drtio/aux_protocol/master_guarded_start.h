/* SPDX-License-Identifier: LGPL-3.0-or-later */
#pragma once
#include "master_profile_bind.h"
#include "master_async_setup.h"
/* Offline composition: same software grant from first profile read to held
 * completion. One bus callback/step including profile binding. No runtime
 * hooks, physical lease/readiness detection or AXI/decoder fault containment.
 * Zero initialize, single foreground owner; no concurrent/reentrant operations.
 */
enum mfg_phase {MFG_PROFILE,MFG_SETUP,MFG_COMPLETE,MFG_FAILED};
enum mfg_error {MFG_INVALID=-60,MFG_CANCELLED=-61,MFG_STALE=-62};
struct mfg_start {struct mfo_gate *gate;uint64_t ticket,epoch;struct mm_transport mm;struct mmb_session bind;struct mau_setup setup;uint32_t action_budget,routing_budget,total_budget;unsigned started;enum mfg_phase phase;int error;};
static inline int mfg_same_owner(const struct mfg_start *s){return s&&s->started&&s->gate&&s->gate->owner==MFO_MASTER_OWNER&&s->gate->ticket==s->ticket&&s->gate->epoch==s->epoch;}
static inline int mfg_stale(struct mfg_start *s){s->phase=MFG_FAILED;s->error=MFG_STALE;return s->error;}
static inline int mfg_fail(struct mfg_start *s,int error){
 if(!s||!s->started)return MFG_INVALID;
 if(s->phase==MFG_FAILED)return s->error;
 if(!mfg_same_owner(s))return mfg_stale(s);
 if(s->gate->state==MFO_FAULT&&s->gate->error<0)error=s->gate->error;
 s->phase=MFG_FAILED;s->error=error<0?error:MFG_INVALID;
 mfo_fault(s->gate,s->error);mmb_cancel(&s->bind);mau_cancel(&s->setup);
 s->mm.bound=0;s->mm.failed=1;return s->error;
}
static inline int mfg_begin(struct mfg_start *s,struct mfo_gate *g,uint64_t ticket,const struct mm_bus *bus,uint32_t poll_budget,uint32_t action_budget,uint32_t routing_budget,uint32_t total_setup_budget){
 if(!s||s->started||!action_budget||action_budget>4096||!routing_budget||routing_budget>10000000||!total_setup_budget||total_setup_budget>10000000)return MFG_INVALID;
 int valid=mmb_validate(g,ticket,&s->mm,bus,poll_budget);if(valid)return valid;
 struct mm_bus bus_copy=*bus; /* May alias s->mm.bus, preserve before zeroing. */
 unsigned char *storage=(unsigned char *)s;
 for(size_t i=0;i<sizeof(*s);i++){storage[i]=0;}
 s->gate=g;s->ticket=ticket;s->epoch=g->epoch;s->action_budget=action_budget;
 s->routing_budget=routing_budget;s->total_budget=total_setup_budget;s->phase=MFG_PROFILE;
 int r=mmb_begin(&s->bind,g,ticket,&s->mm,&bus_copy,poll_budget);if(r)return r;
 s->started=1;return 0;
}
static inline int mfg_cancel(struct mfg_start *s){return mfg_fail(s,MFG_CANCELLED);}
static inline int mfg_step(struct mfg_start *s){
 if(!s||!s->started)return MFG_INVALID;
 if(s->phase==MFG_FAILED)return s->error;
 if(!mfg_same_owner(s))return mfg_stale(s);
 if(s->gate->state==MFO_FAULT)return mfg_fail(s,s->gate->error);
 if(s->phase==MFG_COMPLETE){
  if(s->gate->state!=MFO_HELD||!mm_ready(&s->mm)||s->gate->profile_ticket!=s->ticket||s->gate->setup_ticket!=s->ticket)return mfg_fail(s,MFG_INVALID);
  return 1;
 }
 int r;
 if(s->phase==MFG_PROFILE){
  r=mmb_step(&s->bind);
  if(s->phase==MFG_FAILED)return s->error;
  if(!mfg_same_owner(s))return mfg_stale(s);
  if(r<0)return mfg_fail(s,r);
  if(r==1){int opened=mau_begin(&s->setup,s->gate,s->ticket,&s->mm,s->action_budget,s->routing_budget,s->total_budget);if(opened)return mfg_fail(s,opened);s->phase=MFG_SETUP;}
  return 0; /* No setup IO in same turn as final profile read. */
 }
 if(s->phase==MFG_SETUP){
  if(!mm_ready(&s->mm)||s->gate->profile_ticket!=s->ticket||s->gate->setup_ticket!=s->ticket)return mfg_fail(s,MFG_INVALID);
  r=mau_step(&s->setup);
  if(s->phase==MFG_FAILED)return s->error;
  if(!mfg_same_owner(s))return mfg_stale(s);
  if(r<0)return mfg_fail(s,r);
  if(r==1){s->phase=MFG_COMPLETE;return 1;}
  return 0;
 }
 return mfg_fail(s,MFG_INVALID);
}
