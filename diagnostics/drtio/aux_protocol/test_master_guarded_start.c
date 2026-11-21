/* SPDX-License-Identifier: LGPL-3.0-or-later */
#ifdef MASTER_A53_EMULATION
extern void master_emulation_assert(int);
extern void master_emulation_guarded_start_pass(unsigned);
#define assert(condition) master_emulation_assert(!!(condition))
#else
#include <assert.h>
#include <stdio.h>
#endif
#include "master_guarded_start.h"
#include "master_setup_mock_fixture.h"
struct fixture {struct setup_fake fake;struct mfg_start *start;struct mfo_gate *gate;uint64_t ticket;unsigned scenario;};
static int after_bus(struct fixture *f,int error,uint32_t *v){
 if(f->start->phase==MFG_PROFILE){
  unsigned index=f->start->bind.index+1,n=f->scenario;
  if(n>=2&&n<=4&&index==n-1)*v^=1;
  if(n>=5&&n<=7&&index==n-4)error=-1;
  if(n>=8&&n<=10&&index==n-7)assert(mfg_cancel(f->start)==MFG_CANCELLED);
  if(n==11){f->gate->ticket++;f->gate->epoch++;f->start->mm.bound=1;f->start->mm.budget=99;}
 }else if(f->scenario==15&&f->start->setup.phase==MS_ROUTING&&f->fake.tx==129){assert(mfg_cancel(f->start)==MFG_CANCELLED);}
 return error;
}
static int read_reg(void *ctx,uint32_t a,uint32_t *v){struct fixture *f=ctx;assert(f->gate->state==MFO_MASTER&&f->gate->ticket==f->ticket);if(f->start->phase==MFG_PROFILE)assert(!f->start->mm.bound&&!f->start->setup.started);return after_bus(f,setup_read(&f->fake,a,v),v);}
static int write_reg(void *ctx,uint32_t a,uint32_t v){struct fixture *f=ctx;assert(f->start->phase==MFG_SETUP&&f->start->mm.bound&&f->gate->state==MFO_MASTER);uint32_t unused=0;return after_bus(f,setup_write(&f->fake,a,v),&unused);}
static int fence(void *ctx){struct fixture *f=ctx;assert(f->start->phase==MFG_SETUP&&f->start->mm.bound&&f->gate->state==MFO_MASTER);uint32_t unused=0;return after_bus(f,setup_fence(&f->fake),&unused);}
int master_guarded_start_test(const uint8_t *frames,size_t size){
 (void)action_step;assert(size==40);unsigned cases=0;
 for(unsigned n=0;n<24;n++){
  struct mfo_gate gate;mfo_init(&gate);struct mfg_start start={0};struct fixture f={.fake={.frames=frames,.mode=n==1?12:n==14?9:0,.failed_route_stage=127},.start=&start,.gate=&gate,.scenario=n};
  struct mm_bus bus={&f,read_reg,write_reg,fence};assert(mfg_begin(&start,&gate,1,&bus,3,64,8730,8827)==MMB_INVALID&&!f.fake.calls&&!start.started);
  assert(!mfo_fresh_epoch(&gate,1,15)&&!mfo_request_master(&gate)&&!mfo_grant_master(&gate,7));f.ticket=gate.ticket;
  assert(!mfg_begin(&start,&gate,gate.ticket,&bus,3,64,n==16?8729:8730,n==17?8826:n==1?8831:8827)&&!f.fake.calls&&!start.mm.bound&&!start.setup.started);
  struct mfg_start replay={0};assert(mfg_begin(&replay,&gate,gate.ticket,&bus,3,64,8730,8827)==MMB_BUSY&&!replay.started);
  int result=0;unsigned turns=0,management=0;
  while(!result){
   management++;assert(mfo_worker_dispatch(&gate)==MFO_BUSY);
   if(start.phase==MFG_SETUP&&turns==3&&n==12)assert(mfg_cancel(&start)==MFG_CANCELLED);
   if(start.phase==MFG_SETUP&&turns==3&&n==13)assert(mfo_fault(&gate,-88)==-88&&mfg_cancel(&start)==-88);
   if(start.phase==MFG_SETUP&&turns==3&&n==23){gate.profile_ticket=0;}
   unsigned before=f.fake.calls;result=mfg_step(&start);assert(f.fake.calls-before<=1&&++turns<8840);
  }
  assert(turns==management);
#ifdef FORCE_GUARDED_START_ASSERT
  if(n==0)assert(turns==8829); /* Deliberately false: healthy uses8830. */
#endif
  if(n==0||n==1||n==18||(n>=19&&n<=22)){assert(result==1&&start.phase==MFG_COMPLETE&&gate.state==MFO_HELD&&start.mm.bound&&start.setup.rt.credits==16&&f.fake.tx==259&&f.fake.pops==260&&turns==(n==1?8834u:8830u));}
  else if(n==11){assert(result==MFG_STALE&&gate.state==MFO_MASTER&&start.mm.bound&&!start.mm.failed&&start.mm.budget==99&&!start.setup.started);}
  else {assert(result<0&&start.phase==MFG_FAILED&&gate.state==MFO_FAULT&&!start.mm.bound&&start.mm.failed&&!start.setup.rt.credits);}
  if(n>=2&&n<=10){assert(!start.setup.started&&!f.fake.tx&&!f.fake.pops);}
  if(n==12||n==13){assert(!f.fake.tx&&!f.fake.pops&&f.fake.calls==3);}
  if(n==23){assert(result==MFG_INVALID&&f.fake.calls==3&&!f.fake.tx);}
  if(n==15){assert(result==MFG_CANCELLED&&f.fake.tx==129&&f.fake.pops==129&&f.fake.present);}
  unsigned calls=f.fake.calls;assert(mfg_step(&start)==result&&f.fake.calls==calls);
  if(n>=19&&n<=22){
   if(n==19){gate.profile_ticket=0;}else if(n==20){gate.setup_ticket=0;}else if(n==21){start.mm.bound=0;}else{gate.state=MFO_MASTER;}
   assert(mfg_step(&start)==MFG_INVALID&&gate.state==MFO_FAULT&&!start.mm.bound&&start.mm.failed&&!start.setup.rt.credits&&f.fake.calls==calls);
  }
  else if(n==18){assert(!mfo_release_master(&gate,gate.ticket,7)&&!mfo_worker_dispatch(&gate));assert(mfg_cancel(&start)==MFG_STALE&&gate.state==MFO_WORKER&&!start.mm.failed&&start.mm.bound&&f.fake.calls==calls);}
  else if(result==1){assert(mfg_cancel(&start)==MFG_CANCELLED&&gate.state==MFO_FAULT&&!start.mm.bound&&start.mm.failed&&!start.setup.rt.credits&&f.fake.calls==calls);}
  cases++;
 }
#ifdef MASTER_A53_EMULATION
 master_emulation_guarded_start_pass(cases);
#else
 printf("MASTER_GUARDED_START_PASS cases=%u healthy_turns=8830 max_callbacks_per_turn=1\n",cases);
#endif
 return 0;
}
