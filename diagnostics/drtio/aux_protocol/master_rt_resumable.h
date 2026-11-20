/* SPDX-License-Identifier: LGPL-3.0-or-later */
#pragma once
#include "master_rt_setup.h"
/* Isolated offline backend. Zero-initialize session once per qualified epoch.
 * At most ONE read/write/fence callback per step, not a wall-time guarantee.
 * Caller owns CRI exclusively throughout; a callback can still hang in AXI.
 * No target reset, retry, automatic cleanup or fresh-epoch detection here.
 */
enum mrs_kind {MRS_TIME=1,MRS_BUFFER};
enum mrs_error {MRS_INVALID=-1,MRS_IO=-2,MRS_TIMEOUT=-3,MRS_CANCELLED=-4};
struct mrs_session {struct mrt_setup *rt;enum mrs_kind kind;unsigned started,phase;int terminal;uint32_t left,before,busy,space;};
static inline int mrs_fail(struct mrs_session *s,int error){
 if(!s)return MRS_INVALID;
 if(!s->terminal)s->terminal=error<0?error:MRS_INVALID;
 return s->terminal;
}
static inline int mrs_begin(struct mrs_session *s,struct mrt_setup *rt,enum mrs_kind kind,unsigned reviewed_epoch){
 if(!s||s->started||!rt||!mm_ready(rt->mm)||reviewed_epoch!=1||
  (kind!=MRS_TIME&&kind!=MRS_BUFFER)||!rt->mm->budget)return MRS_INVALID;
 if((kind==MRS_TIME&&rt->time_attempted)||(kind==MRS_BUFFER&&(rt->force_attempted||rt->request_attempted||rt->credits)))return MRS_INVALID;
 *s=(struct mrs_session){.rt=rt,.kind=kind,.started=1,.left=rt->mm->budget};return 0;
}
static inline void mrs_cancel(struct mrs_session *s){if(s&&s->started&&!s->terminal)mrs_fail(s,MRS_CANCELLED);}
static inline int mrs_step(struct mrs_session *s){
 if(!s||!s->started)return MRS_INVALID;
 if(s->terminal)return s->terminal;
 struct mrt_setup *r=s->rt;struct mm_transport *m=r->mm;
 if(!mm_ready(m))return mrs_fail(s,MRS_IO);
 unsigned phase=s->phase,op=0;uint32_t a=0,v=0; /* op: read0, write1, fence2 */
 if(s->kind==MRS_TIME){
  switch(phase){
   case 0:case 6:a=MRT_RX_UP;break;
   case 1:case 7:a=MRT_ERROR;break;
   case 2:case 5:a=MRT_SET_TIME;break;
   case 3:a=MRT_SET_TIME;v=1;op=1;r->time_attempted=1;break;
   case 4:op=2;break;
   default:return mrs_fail(s,MRS_INVALID);
  }
 }else{
  switch(phase){
   case 0:case 14:a=MRT_RX_UP;break;
   case 1:case 15:a=MRT_ERROR;break;
   case 2:case 9:case 19:a=MRT_FORCE;break;
   case 3:case 12:a=MRT_WAIT;break;
   case 4:case 13:a=MRT_COUNT;break;
   case 5:a=MRT_DEST;v=1;op=1;break;
   case 6:case 8:case 11:case 18:op=2;break;
   case 7:a=MRT_FORCE;v=1;op=1;r->force_attempted=1;break;
   case 10:a=MRT_BUFFER;v=1;op=1;r->request_attempted=1;break;
   case 16:a=MRT_SPACE;break;
   case 17:a=MRT_FORCE;v=0;op=1;r->unforce_attempted=1;break;
   default:return mrs_fail(s,MRS_INVALID);
  }
 }
 int error=op==0?m->bus.read(m->bus.ctx,a,&v):op==1?m->bus.write(m->bus.ctx,a,v):m->bus.fence(m->bus.ctx);
 /* A synchronous callback cancellation wins, preserving attempted flags. */
 if(s->terminal){if(error)mm_fail(m);return s->terminal;}
 if(error){mm_fail(m);return mrs_fail(s,MRS_IO);}
 if(s->kind==MRS_TIME){
  if((phase==0||phase==6)&&v!=1)return mrs_fail(s,MRS_IO);
  if((phase==1||phase==7)&&v)return mrs_fail(s,MRS_IO);
  if(phase==2&&v)return mrs_fail(s,MRS_IO);
  if(phase==5){if(v>1)return mrs_fail(s,MRS_IO);if(v)return --s->left?0:mrs_fail(s,MRS_TIMEOUT);}
  if(phase==7){s->terminal=1;return 1;}
 }else{
  if((phase==0||phase==14)&&v!=1)return mrs_fail(s,MRS_IO);
  if((phase==1||phase==15||phase==2||phase==3||phase==19)&&v)return mrs_fail(s,MRS_IO);
  if(phase==4)s->before=v;
  if(phase==9&&v!=1)return mrs_fail(s,MRS_IO);
  if(phase==12){if(v>1)return mrs_fail(s,MRS_IO);s->busy=v;}
  if(phase==13){
   uint32_t delta=v-s->before;if(delta>1)return mrs_fail(s,MRS_IO);
   if(s->busy||delta!=1){if(!--s->left)return mrs_fail(s,MRS_TIMEOUT);s->phase=12;return 0;}
  }
  if(phase==16){if(!v||v>65535)return mrs_fail(s,MRS_IO);s->space=v;}
  if(phase==19){r->credits=s->space;s->terminal=1;return 1;}
 }
 s->phase++;return 0;
}
