/* SPDX-License-Identifier: LGPL-3.0-or-later */
#pragma once
#include "master_network_admission.h"
#include "master_guarded_start.h"
/* Isolated single-use composition, NOT production service. The observer reads
 * a qualified memory publication only, never MMIO/network IO or the worker.
 * It must return a coherent fresh observation; synchronization/ISR publisher
 * and IRQ/nesting/in-flight fault containment are external requirements.
 * Step result1 is tentative; only a fresh mnh_snapshot may publish success.
 * Never publish internal start credits directly.
 * Sole foreground; active rejects synchronous recursion, not threads/IRQs.
 */
struct mnh_health {uint64_t generation;unsigned receipts;int fault;};
typedef int (*mnh_observer)(void *,struct mnh_health *);
struct mnh_status {unsigned complete;uint32_t credits;int error;};
struct mnh_start {struct mfg_start start;struct mne_policy policy;mnh_observer observe;void *observer_ctx;unsigned started,active;int error;};
enum mnh_error {MNH_INVALID=-90};
static inline int mnh_fail(struct mnh_start *p,int error){
 if(!p->error)p->error=error<0?error:MNH_INVALID;
 if(p->start.started)mfg_cancel(&p->start); /* Fault/stale path: memory only. */
 return p->error;
}
static inline int mnh_health_check(struct mnh_start *p){
 struct mnh_health h={0};int failed=p->observe(p->observer_ctx,&h);
 int r=mne_observe(&p->policy,failed?0:h.generation,failed?0:h.receipts,failed?1:h.fault);
 return r?mnh_fail(p,r):0;
}
static inline int mnh_begin(struct mnh_start *p,struct mfo_gate *gate,uint64_t ticket,const struct mm_bus *bus,void *ctx,mnh_observer observe,uint32_t poll,uint32_t action,uint32_t route,uint32_t total){
 if(!p)return MNH_INVALID;
 if(p->active)return MFO_BUSY;
 if(p->started||!observe)return MNH_INVALID;
 p->started=1;p->active=1;p->observe=observe;p->observer_ctx=ctx;
 struct mnh_health h={0};int failed=observe(ctx,&h);
 int r=mne_begin(&p->policy,gate,ticket,failed?0:h.generation,failed?0:h.receipts,failed?1:h.fault);
 if(!r){r=mfg_begin(&p->start,gate,ticket,bus,poll,action,route,total);if(r)mfo_fault(gate,r);}
 if(r)mnh_fail(p,r);
 p->active=0;return r;
}
static inline int mnh_step(struct mnh_start *p){
 if(!p||!p->started)return MNH_INVALID;
 if(p->active)return MFO_BUSY;
 if(p->error)return p->error;
 p->active=1;int r=mnh_health_check(p);
 if(!r){
  r=mfg_step(&p->start);
  /* Always inspect health after the step, including candidate completion. */
  int health=mnh_health_check(p);if(health)r=health;
  else if(r<0)mnh_fail(p,r);
 }
 p->active=0;return r;
}
static inline int mnh_snapshot(struct mnh_start *p,struct mnh_status *out){
 if(!p)return MNH_INVALID;
 if(p->active)return MFO_BUSY;
 if(!p->started||!out)return MNH_INVALID;
 p->active=1;int r=p->error?p->error:mnh_health_check(p);
 *out=(struct mnh_status){.error=r};
 if(!r&&p->start.phase==MFG_COMPLETE){
  struct mfg_start *s=&p->start;
  if(!mne_ready(&p->policy)||!mm_ready(&s->mm)||s->gate->state!=MFO_HELD||s->gate->profile_ticket!=s->ticket||s->gate->setup_ticket!=s->ticket){
   mne_observe(&p->policy,0,0,1);r=mnh_fail(p,MNH_INVALID);out->error=r;
  }else{out->complete=1;out->credits=s->setup.rt.credits;}
 }
 p->active=0;return r;
}
