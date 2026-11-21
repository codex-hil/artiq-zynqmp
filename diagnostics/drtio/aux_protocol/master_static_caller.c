/* SPDX-License-Identifier: LGPL-3.0-or-later */
#include "master_static_caller.h"
_Alignas(64) static struct mfg_start mfc_context;
int mfc_begin(struct mfo_gate *gate,uint64_t ticket,const struct mm_bus *bus,uint32_t poll,uint32_t action,uint32_t route,uint32_t total){
 if(mfc_context.started)return MFO_BUSY; /* No implicit restart, even after fault/new epoch. */
 return mfg_begin(&mfc_context,gate,ticket,bus,poll,action,route,total);
}
int mfc_poll(void){return mfg_step(&mfc_context);}
int mfc_cancel(void){return mfg_cancel(&mfc_context);}
int mfc_snapshot(struct mfc_status *out){
 if(!out)return MFG_INVALID;
 struct mfg_start *s=&mfc_context;
 *out=(struct mfc_status){.initialized=s->started,.phase=s->phase,.result=MFG_INVALID,.ticket=s->ticket,.epoch=s->epoch};
 if(!s->started)return 0;
 out->routing_completed=s->setup.routing.completed;
 if(s->phase==MFG_FAILED){out->result=s->error;return 0;}
 if(!mfg_same_owner(s)){out->result=MFG_STALE;return 0;}
 if(s->gate->state==MFO_FAULT){out->result=s->gate->error;return 0;}
 out->profile_bound=mm_ready(&s->mm)&&s->gate->profile_ticket==s->ticket;
 if(s->phase==MFG_COMPLETE){
  out->candidate_complete=out->profile_bound&&s->gate->state==MFO_HELD&&s->gate->setup_ticket==s->ticket;
  out->result=out->candidate_complete?1:MFG_INVALID;
  if(out->candidate_complete)out->credits=s->setup.rt.credits;
 }else out->result=0;
 return 0;
}
