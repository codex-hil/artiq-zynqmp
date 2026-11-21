/* SPDX-License-Identifier: LGPL-3.0-or-later */
#include <assert.h>
#include <stdio.h>
#include "master_profile_bind.h"
struct fake {struct mmb_session *s;struct mfo_gate *g;struct mm_transport *destination;unsigned calls,mode,cut;};
static int read_reg(void *ctx,uint32_t a,uint32_t *v){
 struct fake *f=ctx;assert(f->g->state==MFO_MASTER&&!f->destination->bound&&f->g->profile_ticket==f->g->ticket);
 assert(a==0xa0000800+4*f->calls);f->calls++;const uint32_t expected[3]={0x47534d31,3,125000000};*v=expected[f->calls-1];
 if(f->calls==f->cut){
  if(f->mode==1)*v^=1;
  if(f->mode==2)return -1;
  if(f->mode==3)assert(mmb_cancel(f->s)==MMB_CANCELLED);
  if(f->mode==4)assert(mfo_fault(f->g,-77)==-77);
  if(f->mode==6)f->g->state=MFO_HELD;
  if(f->mode==7)f->g->setup_ticket=f->g->ticket;
  if(f->mode==8)f->g->profile_ticket=0;
  if(f->mode==5){f->g->ticket++;f->g->epoch++;f->destination->bound=1;f->destination->budget=99;}
 }
 return 0;
}
static int write_reg(void *ctx,uint32_t a,uint32_t v){(void)ctx;(void)a;(void)v;assert(0);return -1;}
static int fence(void *ctx){(void)ctx;assert(0);return -1;}
static struct mfo_gate grant(void){struct mfo_gate g;mfo_init(&g);assert(!mfo_fresh_epoch(&g,1,15)&&!mfo_request_master(&g)&&!mfo_grant_master(&g,7));return g;}
int main(void){
 unsigned cases=0;
 for(unsigned mode=0;mode<=8;mode++)for(unsigned cut=1;cut<=3;cut++){
  struct mfo_gate g=grant();struct mm_transport destination={0};struct mmb_session s={0};struct fake f={&s,&g,&destination,0,mode,cut};struct mm_bus bus={&f,read_reg,write_reg,fence};
  assert(!mmb_begin(&s,&g,g.ticket,&destination,&bus,3)&&!f.calls&&!destination.bound);
  struct mmb_session replay={0};assert(mmb_begin(&replay,&g,g.ticket,&destination,&bus,3)==MMB_BUSY&&!replay.started);
  int result=0;while(!result){unsigned before=f.calls;result=mmb_step(&s);assert(f.calls-before==1);if(!result)assert(!destination.bound);}
  if(mode==0){assert(result==1&&f.calls==3&&destination.bound&&!destination.failed&&destination.budget==3&&g.state==MFO_MASTER);}
  else if(mode==5){assert(result==MMB_STALE&&f.calls==cut&&destination.bound&&destination.budget==99&&!destination.failed&&g.state==MFO_MASTER);}
  else {assert(result<0&&f.calls==cut&&!destination.bound&&destination.failed&&g.state==MFO_FAULT);}
  if(mode==4)assert(result==-77&&mmb_cancel(&s)==-77);
  unsigned calls=f.calls;assert(mmb_step(&s)==result&&f.calls==calls);
  if(mode==0){assert(mmb_cancel(&s)==MMB_CANCELLED&&!destination.bound&&destination.failed&&g.state==MFO_FAULT&&f.calls==calls);}
  cases++;
 }
 /* No grant, partial dispatch/ownership state, malformed bus/budget: zero IO. */
 for(unsigned state=MFO_CLOSED;state<=MFO_FAULT;state++)if(state!=MFO_MASTER){
  struct mfo_gate g=grant();g.state=(enum mfo_state)state;struct mm_transport d={0};struct mmb_session s={0};struct fake f={&s,&g,&d,0,0,0};struct mm_bus b={&f,read_reg,write_reg,fence};
  assert(mmb_begin(&s,&g,g.ticket,&d,&b,3)==MMB_INVALID&&!f.calls&&!s.started);cases++;
 }
 for(unsigned between=0;between<=2;between++){
  struct mfo_gate g=grant();struct mm_transport d={0};struct mmb_session s={0};struct fake f={&s,&g,&d,0,0,0};struct mm_bus b={&f,read_reg,write_reg,fence};
  assert(!mmb_begin(&s,&g,g.ticket,&d,&b,3));for(unsigned i=0;i<between;i++)assert(!mmb_step(&s));
  g.ticket++;g.epoch++;d.bound=1;d.budget=99;assert(mmb_step(&s)==MMB_STALE&&f.calls==between&&d.bound&&d.budget==99&&!d.failed);cases++;
 }
 for(unsigned bad=0;bad<6;bad++){
  struct mfo_gate g=grant();struct mm_transport d={0};struct mmb_session s={0};struct fake f={&s,&g,&d,0,0,0};struct mm_bus b={&f,read_reg,write_reg,fence};
  uint32_t budget=bad==0?0:bad==1?1025:3;if(bad==2)b.read=0;if(bad==3)b.write=0;if(bad==4)b.fence=0;if(bad==5)d.failed=1;
  assert(mmb_begin(&s,&g,g.ticket,&d,&b,budget)==MMB_INVALID&&!f.calls&&!s.started&&!g.profile_ticket);cases++;
 }
 printf("MASTER_PROFILE_BIND_PASS cases=%u max_callbacks_per_turn=1 ready_after_reads=3\n",cases);return 0;
}
