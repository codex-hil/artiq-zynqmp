/* SPDX-License-Identifier: LGPL-3.0-or-later */
#pragma once
#include "master_foreground_owner.h"
#include "master_async_star.h"
#include "master_control_codec.h"
#include "master_rt_resumable.h"
#include "master_setup_sequence.h"
/* Separate offline whole-setup coordinator. mm_bind/profile qualification must
 * already have occurred under this master grant; bind is NOT resumable here.
 * One bus callback maximum per step AFTER begin, with CPU-only encode/decode
 * turns. All production worker admission/epoch/latency/recovery obligations
 * remain external. Completion retains ownership, never publishes network UP.
 */
enum mau_error {MAU_INVALID=-40,MAU_BUDGET=-41,MAU_CANCELLED=-42,MAU_STALE=-43};
struct mau_setup {
 struct mfo_gate *gate;struct mm_transport *mm;uint64_t ticket,epoch;
 struct map_request control;struct mar_session tsc;struct mas_table routing;
 struct mrt_setup rt;struct mrs_session time,buffer;
 uint32_t action_budget,action_left,routing_budget,total_left;
 unsigned started,link_phase,time_precheck;enum ms_action phase;int error;
};
static inline int mau_same_owner(const struct mau_setup *s){
 return s&&s->started&&s->gate&&s->gate->ticket==s->ticket&&s->gate->epoch==s->epoch&&s->gate->owner==MFO_MASTER_OWNER;
}
static inline int mau_stale(struct mau_setup *s){
 /* Do not poison/release a transport possibly now assigned to another owner. */
 s->phase=MS_FAILED;s->error=MAU_STALE;s->rt.credits=0;return s->error;
}
static inline int mau_fail(struct mau_setup *s,int error){
 if(!s||!s->started)return MAU_INVALID;
 if(s->phase==MS_FAILED)return s->error;
 if(!mau_same_owner(s))return mau_stale(s);
 if(s->gate->state==MFO_FAULT&&s->gate->error<0)error=s->gate->error;
 s->phase=MS_FAILED;s->error=error<0?error:MAU_INVALID;s->rt.credits=0;
 map_cancel(&s->control);mar_cancel(&s->tsc);mas_cancel(&s->routing);mrs_cancel(&s->time);mrs_cancel(&s->buffer);
 mm_fail(s->mm);mfo_fault(s->gate,s->error);return s->error;
}
static inline int mau_begin(struct mau_setup *s,struct mfo_gate *g,uint64_t ticket,struct mm_transport *m,uint32_t action_budget,uint32_t routing_budget,uint32_t total_budget){
 if(!s||s->started||!g||!ticket||g->ticket!=ticket||g->state!=MFO_MASTER||g->owner!=MFO_MASTER_OWNER||!mm_ready(m)||m->held||!action_budget||action_budget>4096||!routing_budget||routing_budget>10000000||!total_budget||total_budget>10000000)return MAU_INVALID;
 if(g->setup_ticket==ticket)return MFO_BUSY;
 *s=(struct mau_setup){.gate=g,.mm=m,.ticket=ticket,.epoch=g->epoch,.action_budget=action_budget,.action_left=action_budget,.routing_budget=routing_budget,.total_left=total_budget,.started=1,.phase=MS_LINK};
 s->rt.mm=m;g->setup_ticket=ticket;return 0;
}
static inline int mau_cancel(struct mau_setup *s){return mau_fail(s,MAU_CANCELLED);}
static inline int mau_action(struct mau_setup *s){
 struct mm_transport *m=s->mm;uint32_t v;
 switch(s->phase){
  case MS_LINK:
   if(mm_read(m,s->link_phase?MRT_ERROR:MRT_RX_UP,&v)||v!=(s->link_phase?0u:1u))return MAU_INVALID;
   return ++s->link_phase==2?1:0;
  case MS_ECHO:case MS_STATUS:
   if(!s->control.started){
    uint8_t bytes[8];int n=aux_master_control_encode(s->phase==MS_ECHO?0:0x20,s->phase==MS_ECHO?0:1,bytes,sizeof(bytes));
    if(n!=8)return MAU_INVALID;
    return map_begin(&s->control,m,bytes,8,aux_master_control_decode,s->phase==MS_ECHO?1:0x22,1);
   }
   return map_step(&s->control);
  case MS_SET_TIME:
   if(s->time_precheck<2){
    if(mm_read(m,s->time_precheck?MM_RX_PRESENT:MM_RX_ERROR,&v)||v)return MAU_INVALID;
    s->time_precheck++;return 0;
   }
   if(!s->time.started&&mrs_begin(&s->time,&s->rt,MRS_TIME,1))return MAU_INVALID;
   return mrs_step(&s->time);
  case MS_TSC_ACK:
   if(!s->tsc.started&&mar_begin(&s->tsc,m,aux_master_control_decode,1))return MAU_INVALID;
   {int r=mar_step(&s->tsc);return r==1&&s->tsc.kind!=4?MAP_UNEXPECTED:r;}
  case MS_ROUTING:
   if(!s->routing.started&&mas_begin(&s->routing,m,s->routing_budget,1))return MAU_INVALID;
   return mas_step(&s->routing);
  case MS_BUFFER:
   if(!s->buffer.started&&mrs_begin(&s->buffer,&s->rt,MRS_BUFFER,1))return MAU_INVALID;
   return mrs_step(&s->buffer);
  default:return MAU_INVALID;
 }
}
static inline int mau_step(struct mau_setup *s){
 if(!s||!s->started)return MAU_INVALID;
 if(s->phase==MS_FAILED)return s->error;
 if(!mau_same_owner(s))return mau_stale(s);
 if(s->gate->state==MFO_FAULT)return mau_fail(s,s->gate->error);
 if(s->phase==MS_COMPLETE&&s->gate->state==MFO_HELD)return 1;
 if(s->gate->state!=MFO_MASTER||!mm_ready(s->mm))return mau_fail(s,MAU_INVALID);
 if(!s->total_left||(s->phase!=MS_ROUTING&&!s->action_left))return mau_fail(s,MAU_BUDGET);
 s->total_left--;if(s->phase!=MS_ROUTING)s->action_left--;
 int r=mau_action(s);
 if(s->phase==MS_FAILED)return s->error; /* Synchronous cancellation wins. */
 if(!mau_same_owner(s))return mau_stale(s);
 if(s->gate->state==MFO_FAULT)return mau_fail(s,s->gate->error);
 if(r<0)return mau_fail(s,r);
 if(r>1)return mau_fail(s,MAU_INVALID);
 if(r==1){
  if(s->phase==MS_BUFFER){int held=mfo_setup_result(s->gate,s->ticket,1);if(held)return mau_fail(s,held);s->phase=MS_COMPLETE;return 1;}
  if(s->phase==MS_ECHO)s->control=(struct map_request){0}; /* Distinct later STATUS only after ECHO ack/pop. */
  s->phase=(enum ms_action)(s->phase+1);s->action_left=s->action_budget;
 }
 if(!s->total_left||(s->phase!=MS_ROUTING&&!s->action_left))return mau_fail(s,MAU_BUDGET);
 return 0;
}
