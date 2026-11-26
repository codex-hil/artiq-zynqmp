/* SPDX-License-Identifier: LGPL-3.0-or-later */
#ifdef MASTER_A53_EMULATION
extern void master_emulation_assert(int);
extern void master_emulation_network_latch_pass(unsigned);
#define assert(condition) master_emulation_assert(!!(condition))
#else
#include <assert.h>
#include <stdio.h>
#endif
#include "master_network_fault_observer.h"
#include "master_setup_mock_fixture.h"
struct latch_fixture {struct setup_fake fake;struct mnh_start *start;struct mnf_latch *latch;unsigned scenario,published;};
static void after_bus(struct latch_fixture *f){
 if(f->published)return;
 unsigned n=f->scenario;
 if((n==3&&f->fake.calls==1)||(n==4&&f->fake.calls==3)||(n==5&&f->fake.tx==1)||(n==6&&f->fake.tx==129)||(n==7&&f->fake.tx==258)||(n==8&&f->start->start.setup.phase==MS_BUFFER&&f->start->start.setup.buffer.phase==19)){
  mnf_publish(f->latch);f->published=1;
 }
}
static int rd(void *ctx,uint32_t a,uint32_t *v){struct latch_fixture *f=ctx;int r=setup_read(&f->fake,a,v);after_bus(f);return r;}
static int wr(void *ctx,uint32_t a,uint32_t v){struct latch_fixture *f=ctx;int r=setup_write(&f->fake,a,v);after_bus(f);return r;}
static int fence(void *ctx){struct latch_fixture *f=ctx;int r=setup_fence(&f->fake);after_bus(f);return r;}
int master_network_latch_test(const uint8_t *frames,size_t length){
 (void)action_step;assert(length==40);unsigned cases=0;
 for(unsigned n=0;n<13;n++){
  /* A new object per independent test lifetime, never a reset/rearm API. */
  struct mnf_latch latch=MNF_LATCH_INITIALIZER;
  const struct mnf_view view={&latch,9,n==12?3u:7u};
  struct mfo_gate gate={0};mfo_init(&gate);assert(!mfo_fresh_epoch(&gate,1,15)&&!mfo_request_master(&gate)&&!mfo_grant_master(&gate,7));
  struct mnh_start start={0};struct latch_fixture f={.fake={.frames=frames},.start=&start,.latch=&latch,.scenario=n};struct mm_bus bus={&f,rd,wr,fence};
  if(n==1)mnf_publish(&latch);
  int result=mnh_begin(&start,&gate,gate.ticket,&bus,(void *)&view,mnf_observe,3,64,8730,8827);unsigned turns=0;
  if(n==1||n==12){assert(result==MNE_UNSAFE&&!f.fake.calls&&gate.state==MFO_FAULT);}
  else{
   assert(!result&&!f.fake.calls);
   if(n==2||n==11){mnf_publish(&latch);if(n==11)mnf_publish(&latch);}
   while(!result){unsigned before=f.fake.calls;result=mnh_step(&start);assert(f.fake.calls-before<=1&&++turns<=8830);}
  }
  struct mnh_status out={0};unsigned calls=f.fake.calls;
  if(n==0||n==9||n==10){
   assert(result==1&&turns==8830&&f.fake.tx==259&&f.fake.pops==260);
   if(n==10)assert(!mnh_snapshot(&start,&out)&&out.complete&&out.credits==16);
   if(n==9||n==10)mnf_publish(&latch);
   int r=mnh_snapshot(&start,&out);
   if(n==0)assert(!r&&out.complete&&out.credits==16);
   else assert(r==MNE_UNSAFE&&!out.complete&&!out.credits&&gate.state==MFO_FAULT);
  }else{
   assert(result==MNE_UNSAFE&&gate.state==MFO_FAULT&&gate.owner==MFO_MASTER_OWNER&&mnh_snapshot(&start,&out)==MNE_UNSAFE&&!out.complete&&!out.credits);
   if(n==2||n==11)assert(!calls);
   if(n==3)assert(calls==1&&!f.fake.tx);
   if(n==4)assert(calls==3&&!f.fake.tx);
   if(n==5)assert(f.fake.tx==1);
   if(n==6)assert(f.fake.tx==129);
   if(n==7)assert(f.fake.tx==258);
   if(n==8)assert(turns==8830&&f.fake.tx==259&&f.fake.pops==260);
#ifdef FORCE_NETWORK_LATCH_ASSERT
   if(n==8)assert(out.complete==1); /* Deliberately false after final callback publish. */
#endif
  }
  assert(f.fake.calls==calls);
  if(n!=0){mnf_publish(&latch);assert(mnf_seen(&latch)&&mnh_step(&start)==MNE_UNSAFE&&mnh_snapshot(&start,&out)==MNE_UNSAFE&&!out.complete&&!out.credits&&f.fake.calls==calls);}
  cases++;
 }
#ifdef MASTER_A53_EMULATION
 master_emulation_network_latch_pass(cases);
#else
 printf("MASTER_NETWORK_LATCH_PASS cases=%u healthy_turns=8830 max_callbacks=1\n",cases);
#endif
 return 0;
}
