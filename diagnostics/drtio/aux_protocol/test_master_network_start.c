/* SPDX-License-Identifier: LGPL-3.0-or-later */
#ifdef MASTER_A53_EMULATION
extern void master_emulation_assert(int);
extern void master_emulation_network_start_pass(unsigned);
#define assert(condition) master_emulation_assert(!!(condition))
#else
#include <assert.h>
#include <stdio.h>
#endif
#include "master_network_start.h"
#include "master_setup_mock_fixture.h"
struct fixture {struct setup_fake fake;struct mnh_start *start;struct mfo_gate *gate;struct mnh_health health;unsigned scenario,armed,reads;};
static void after_bus(struct fixture *f){
 if(!f->armed)return;
 if(f->scenario==19&&f->fake.calls==1){mfo_fault(f->gate,-99);assert(!mfo_fresh_epoch(f->gate,2,15)&&!mfo_request_master(f->gate)&&!mfo_grant_master(f->gate,7));f->armed=0;}
 unsigned n=f->scenario;
 if((n==2&&f->fake.calls==1)||(n==3&&f->fake.calls==3)||(n==4&&f->fake.tx==1)||(n==5&&f->fake.tx==129)||(n==6&&f->fake.tx==258)){f->health.generation++;f->armed=0;}
}
static int rd(void *ctx,uint32_t a,uint32_t *v){struct fixture *f=ctx;int r=setup_read(&f->fake,a,v);after_bus(f);return r;}
static int wr(void *ctx,uint32_t a,uint32_t v){struct fixture *f=ctx;int r=setup_write(&f->fake,a,v);after_bus(f);return r;}
static int fence(void *ctx){struct fixture *f=ctx;int r=setup_fence(&f->fake);after_bus(f);return r;}
static int health(void *ctx,struct mnh_health *h){
 struct fixture *f=ctx;f->reads++;
 if(f->scenario==12){
  struct mnh_status out={17,18,19};
  assert(mnh_step(f->start)==MFO_BUSY&&mnh_snapshot(f->start,&out)==MFO_BUSY&&out.complete==17&&out.credits==18&&out.error==19);
 }
 if(f->armed&&f->scenario==7&&f->start->start.phase==MFG_COMPLETE){f->health.generation++;f->armed=0;}
 if(f->scenario==18&&f->armed){mfo_fault(f->gate,-99);assert(!mfo_fresh_epoch(f->gate,2,15)&&!mfo_request_master(f->gate)&&!mfo_grant_master(f->gate,7));f->armed=0;}
 if(f->scenario==10&&f->armed)return -1;
 *h=f->health;return 0;
}
int master_network_start_test(const uint8_t *frames,size_t size){
 (void)action_step;assert(size==40);unsigned cases=0;
 for(unsigned n=0;n<20;n++){
  struct mfo_gate gate={0};mfo_init(&gate);assert(!mfo_fresh_epoch(&gate,1,15)&&!mfo_request_master(&gate)&&!mfo_grant_master(&gate,7));
  struct mnh_start start={0};struct fixture f={.fake={.frames=frames},.start=&start,.gate=&gate,.health={9,7,0},.scenario=n};
  struct mm_bus bus={&f,rd,wr,fence};assert(!mnh_begin(&start,&gate,gate.ticket,&bus,&f,health,3,64,8730,8827)&&!f.fake.calls);f.armed=1;
  assert(mnh_begin(&start,&gate,gate.ticket,&bus,&f,health,3,64,8730,8827)==MNH_INVALID);
  if(n==1)f.health.generation++;
  if(n==9)f.health.receipts=3;
  if(n==13)assert(mfo_fault(&gate,-99)==-99);
  if(n==14)f.health.generation=0;
  if(n==15)f.health.generation=8;
  if(n==16)f.health.receipts=15;
  if(n==17)f.health.fault=1;
  int r=0;unsigned turns=0;
  while(!r){unsigned before=f.fake.calls;r=mnh_step(&start);assert(f.fake.calls-before<=1&&++turns<=8830);}
  unsigned calls=f.fake.calls;struct mnh_status out={0};
  if(n==0||n==8||n==11||n==12){
   assert(r==1&&turns==8830&&gate.state==MFO_HELD&&f.fake.tx==259&&f.fake.pops==260);
   if(n==8||n==11)f.health.generation++;
   int snap=mnh_snapshot(&start,&out);
   if(n==0||n==12){assert(!snap&&out.complete&&out.credits==16&&!out.error);}
   else {assert(snap==MNE_UNSAFE&&!out.complete&&!out.credits&&gate.state==MFO_FAULT);}
  }else if(n>=18){
   assert(r==MNE_STALE&&gate.state==MFO_MASTER&&gate.epoch==2&&gate.ticket!=start.policy.ticket&&!gate.error);
   assert(calls==(n==18?0u:1u)&&mnh_snapshot(&start,&out)==MNE_STALE&&!out.complete&&!out.credits&&mnh_step(&start)==MNE_STALE);
  }else{
   assert(r==(n==13?-99:MNE_UNSAFE)&&gate.state==MFO_FAULT&&!mne_ready(&start.policy)&&start.start.phase==MFG_FAILED&&!start.start.mm.bound&&!start.start.setup.rt.credits);
   assert(mnh_snapshot(&start,&out)==r&&!out.complete&&!out.credits);
   if(n==1||n==9||n>=13||n==10)assert(calls==0);
   if(n==2)assert(calls==1&&!f.fake.tx);
   if(n==3)assert(calls==3&&!f.fake.tx);
   if(n==4)assert(f.fake.tx==1);
   if(n==5)assert(f.fake.tx==129);
   if(n==6)assert(f.fake.tx==258);
   if(n==7)assert(turns==8830&&f.fake.tx==259&&f.fake.pops==260&&!out.complete);
#ifdef FORCE_NETWORK_START_ASSERT
   if(n==7)assert(out.complete==1); /* Deliberately false after late health loss. */
#endif
   assert(mnh_step(&start)==r);
  }
  assert(f.fake.calls==calls);
  if(n==11){assert(!mfo_fresh_epoch(&gate,2,15)&&!mfo_request_master(&gate)&&!mfo_grant_master(&gate,7));uint64_t ticket=gate.ticket;assert(mnh_step(&start)<0&&mnh_snapshot(&start,&out)<0&&!out.complete&&gate.state==MFO_MASTER&&gate.ticket==ticket);}
  cases++;
 }
#ifdef MASTER_A53_EMULATION
 master_emulation_network_start_pass(cases);
#else
 printf("MASTER_NETWORK_START_PASS cases=%u healthy_turns=8830 max_callbacks=1\n",cases);
#endif
 return 0;
}
