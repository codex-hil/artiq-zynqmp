/* SPDX-License-Identifier: LGPL-3.0-or-later */
#ifdef MASTER_A53_EMULATION
extern void master_emulation_assert(int);
extern void master_emulation_async_setup_pass(unsigned);
#define assert(condition) master_emulation_assert(!!(condition))
#else
#include <assert.h>
#include <stdio.h>
#endif
#include "master_async_setup.h"
#include "master_setup_mock_fixture.h"
struct fixture {struct setup_fake fake;struct mau_setup *setup;struct mfo_gate *gate;uint64_t ticket;unsigned scenario,cut;};
static int after_bus(struct fixture *f,int error){
 if(f->setup->started&&f->fake.tx==f->cut+2&&f->setup->phase==MS_ROUTING&&f->scenario>=16&&f->scenario<20){assert(mau_cancel(f->setup)==MAU_CANCELLED);}
 if(f->scenario==20&&f->setup->started&&f->fake.tx==1){assert(mfo_fault(f->gate,-88)==-88);}
 return error;
}
static int read_reg(void *ctx,uint32_t a,uint32_t *v){struct fixture *f=ctx;assert(f->gate->state==MFO_MASTER&&f->gate->ticket==f->ticket);return after_bus(f,setup_read(&f->fake,a,v));}
static int write_reg(void *ctx,uint32_t a,uint32_t v){struct fixture *f=ctx;assert(f->gate->state==MFO_MASTER&&f->gate->ticket==f->ticket);return after_bus(f,setup_write(&f->fake,a,v));}
static int fence(void *ctx){struct fixture *f=ctx;assert(f->gate->state==MFO_MASTER&&f->gate->ticket==f->ticket);return after_bus(f,setup_fence(&f->fake));}
int master_async_setup_test(const uint8_t *frames,size_t size){
 (void)action_step; /* Shared fixture's legacy action callback is not invoked. */
 assert(size==40);const unsigned modes[8]={0,1,2,3,4,5,9,12},cuts[4]={0,127,255,256};unsigned cases=0;
 for(unsigned n=0;n<27;n++){
  struct mfo_gate gate;mfo_init(&gate);assert(!mfo_fresh_epoch(&gate,1,15)&&!mfo_request_master(&gate)&&!mfo_grant_master(&gate,7));
  struct mau_setup setup={0};unsigned cut=n>=8&&n<20?cuts[(n-8)%4]:127;
  struct fixture f={.fake={.frames=frames,.mode=n<8?modes[n]:n<12?8:n<16?9:0,.failed_route_stage=cut},.setup=&setup,.gate=&gate,.ticket=gate.ticket,.scenario=n,.cut=cut};
  struct mm_bus bus={&f,read_reg,write_reg,fence};struct mm_transport mm;assert(!mm_bind(&mm,&bus,3,1));
  unsigned action_budget=n==21?3:64,route_budget=n==22?8729:8730,total_budget=n==23?8826:n==7?8831:8827;
  assert(!mau_begin(&setup,&gate,gate.ticket,&mm,action_budget,route_budget,total_budget));
  struct mau_setup replay={0};assert(mau_begin(&replay,&gate,gate.ticket,&mm,64,8730,8827)==MFO_BUSY&&!replay.started);
  int result=0;unsigned turns=0,management=0;
  while(!result){
   management++;assert(mfo_worker_dispatch(&gate)==MFO_BUSY);
   if(n==25&&f.fake.tx==1){assert(mfo_fault(&gate,-99)==-99&&mau_cancel(&setup)==-99);}
   if(n==24&&f.fake.tx==1){gate.ticket++;gate.epoch++;} /* Old session must not affect new owner/MMIO. */
   unsigned calls=f.fake.calls;result=mau_step(&setup);assert(f.fake.calls-calls<=1&&++turns<=total_budget);
  }
  assert(turns==management);
#ifdef FORCE_ASYNC_SETUP_ASSERT
  if(n==0)assert(turns==8826); /* Deliberately false; healthy uses8827. */
#endif
  if(n==0||n==7||n==26){assert(result==1&&setup.phase==MS_COMPLETE&&gate.state==MFO_HELD&&turns==total_budget&&f.fake.tx==259&&f.fake.pops==260&&setup.routing.completed==257&&setup.rt.credits==16);}
  else {assert(result<0&&setup.phase==MS_FAILED&&!setup.rt.credits);if(n!=24)assert(gate.state==MFO_FAULT&&mm.failed);}
  if(n>=8&&n<20){assert(setup.routing.completed==cut&&f.fake.tx==cut+2&&f.fake.pops==cut+2+(n>=12&&n<16));}
  if(n>=16&&n<20){assert(result==MAU_CANCELLED&&f.fake.present);}
  if(n==20){assert(result==-88&&f.fake.tx==1&&!f.fake.pops);}
  if(n==21){assert(result==MAU_BUDGET&&!f.fake.tx&&!setup.rt.time_attempted);}
  if(n==22){assert(result==MAS_BUDGET&&setup.routing.completed==256&&f.fake.tx==258&&f.fake.pops==259);}
  if(n==23){assert(result==MAU_BUDGET&&f.fake.tx==259&&f.fake.pops==260&&!f.fake.force&&!setup.rt.credits);}
  if(n==25){assert(result==-99&&gate.error==-99&&f.fake.tx==1&&!f.fake.pops);}
  if(n==24){assert(result==MAU_STALE&&gate.state==MFO_MASTER&&!mm.failed);}
  unsigned calls=f.fake.calls;assert(mau_step(&setup)==result&&f.fake.calls==calls);
  if(n==26){assert(mau_cancel(&setup)==MAU_CANCELLED&&gate.state==MFO_FAULT&&mm.failed&&!setup.rt.credits&&f.fake.calls==calls);}
  else if(result==1){assert(!mfo_release_master(&gate,gate.ticket,7)&&!mfo_worker_dispatch(&gate));assert(mau_cancel(&setup)==MAU_STALE&&gate.state==MFO_WORKER&&!mm.failed&&f.fake.calls==calls);}
  else if(n!=24){assert(mau_cancel(&setup)==result&&f.fake.calls==calls);}
  cases++;
 }
#ifdef MASTER_A53_EMULATION
 master_emulation_async_setup_pass(cases);
#else
 printf("MASTER_ASYNC_SETUP_PASS cases=%u healthy_turns=8827 max_callbacks_per_turn=1\n",cases);
#endif
 return 0;
}
