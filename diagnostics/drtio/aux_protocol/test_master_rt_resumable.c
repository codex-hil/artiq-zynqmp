/* SPDX-License-Identifier: LGPL-3.0-or-later */
#include <assert.h>
#include <stdio.h>
#include "master_rt_resumable.h"
struct fake {struct mrs_session *s;unsigned calls,fail_at,cancel_at,mode,polls;uint32_t force,count;};
static int tick(struct fake *f){f->calls++;if(f->calls==f->cancel_at)mrs_cancel(f->s);return f->calls==f->fail_at?-1:0;}
static int read_reg(void *ctx,uint32_t a,uint32_t *v){
 struct fake *f=ctx;if(tick(f))return -1;
 if(a==MRT_RX_UP)*v=f->mode==1?0:1;else if(a==MRT_ERROR)*v=f->mode==2?1:0;
 else if(a==MRT_SET_TIME){*v=f->s->phase==5&&(f->mode==3||(f->mode==4&&f->polls++<2))?1:0;}
 else if(a==MRT_FORCE)*v=f->force;
 else if(a==MRT_WAIT)*v=f->s->phase==12&&f->mode==3?1:0;
 else if(a==MRT_COUNT)*v=f->s->phase==13&&f->mode==7&&f->polls++<2?f->count-1:f->count;
 else {assert(a==MRT_SPACE);*v=f->mode==5?0:16;}
 return 0;
}
static int write_reg(void *ctx,uint32_t a,uint32_t v){
 struct fake *f=ctx;
 if(a==MRT_FORCE)assert(v?f->s->rt->force_attempted:f->s->rt->unforce_attempted);
 if(a==MRT_BUFFER)assert(f->s->rt->request_attempted);
 if(a==MRT_SET_TIME)assert(f->s->rt->time_attempted);
 int error=tick(f); /* Ambiguous failure may already apply. */
 if(a==MRT_FORCE)f->force=v;else if(a==MRT_BUFFER){assert(v==1);f->count+=f->mode==6?2:1;}
 else assert((a==MRT_DEST&&v==1)||(a==MRT_SET_TIME&&v==1));
 return error;
}
static int fence(void *ctx){return tick(ctx);}
int main(void){
 unsigned cases=0;
 for(unsigned kind=1;kind<=2;kind++)for(unsigned mode=0;mode<=7;mode++){
  unsigned normal=kind==MRS_TIME?8:20;
  /* Baseline, each callback failure, each synchronous cancellation. */
  unsigned variants=mode==0?1+normal*2:1;
  for(unsigned variant=0;variant<variants;variant++){
   struct mrs_session s={0};struct fake f={.s=&s,.mode=mode,.count=UINT32_MAX};
   if(variant&&variant<=normal)f.fail_at=variant;
   if(variant>normal)f.cancel_at=variant-normal;
   struct mm_transport mm={.bus={&f,read_reg,write_reg,fence},.budget=3,.bound=1};struct mrt_setup rt={.mm=&mm};
   assert(!mrs_begin(&s,&rt,(enum mrs_kind)kind,1));assert(mrs_begin(&s,&rt,(enum mrs_kind)kind,1)==MRS_INVALID);
   int result=0;unsigned turns=0;
   while(!result){unsigned before=f.calls;result=mrs_step(&s);assert(f.calls-before<=1&&++turns<40);if(f.cancel_at&&f.calls==f.cancel_at)assert(result==MRS_CANCELLED);}
   if(variant)assert(result<0);
   else if(mode==1||mode==2||mode==3||(kind==MRS_BUFFER&&(mode==5||mode==6)))assert(result<0);
   else {assert(result==1);if(kind==MRS_BUFFER)assert(rt.credits==16&&!f.force&&rt.unforce_attempted);}
   if(f.cancel_at)assert(result==MRS_CANCELLED);
   if(variant==0&&mode==0)assert(turns==normal);
   if(kind==MRS_TIME&&mode==4)assert(turns==10&&result==1); /* Final polling unit. */
   if(kind==MRS_BUFFER&&mode==7)assert(turns==24&&result==1); /* Final count polling unit. */
   unsigned calls=f.calls;assert(mrs_step(&s)==result&&f.calls==calls);mrs_cancel(&s);assert(mrs_step(&s)==result&&f.calls==calls);
   if(result<0){assert(!rt.credits);}
   cases++;
  }
 }
 printf("MASTER_RT_RESUMABLE_PASS cases=%u max_callbacks_per_turn=1\n",cases);return 0;
}
