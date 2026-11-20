/* SPDX-License-Identifier: LGPL-3.0-or-later */
#include <assert.h>
#include <stdio.h>
#include "master_rt_resumable.h"
#include "master_foreground_setup.h"
#include "master_setup_mock_fixture.h"
struct resumable_actions {struct action_context base;struct mrs_session time,buffer;unsigned precheck;};
struct resumable_fixture {struct setup_fake fake;struct mfs_session *session;struct resumable_actions *actions;enum ms_action injected_action;unsigned injected_ordinal,action_ops;int cancel;};
static int after_operation(struct resumable_fixture *f,int error){
 enum ms_action action=f->session->setup.plan.action;
 if(action==MS_SET_TIME||action==MS_BUFFER){
  if(action==f->injected_action&&++f->action_ops==f->injected_ordinal){
   if(f->cancel){mrs_cancel(&f->actions->time);mrs_cancel(&f->actions->buffer);assert(mfs_cancel(f->session)==MFO_CANCELLED);}
   else error=-1; /* May already have applied write: no cleanup/retry. */
  }
 }
 return error;
}
static int resumable_read(void *ctx,uint32_t a,uint32_t *v){struct resumable_fixture *f=ctx;assert(mfs_authorized(f->session));return after_operation(f,setup_read(&f->fake,a,v));}
static int resumable_write(void *ctx,uint32_t a,uint32_t v){struct resumable_fixture *f=ctx;assert(mfs_authorized(f->session));return after_operation(f,setup_write(&f->fake,a,v));}
static int resumable_fence(void *ctx){struct resumable_fixture *f=ctx;assert(mfs_authorized(f->session));return after_operation(f,setup_fence(&f->fake));}
static int resumable_action(void *ctx,enum ms_action action,unsigned start){
 struct resumable_actions *c=ctx;
 if(action!=MS_SET_TIME&&action!=MS_BUFFER)return action_step(&c->base,action,start);
 c->base.calls++;if(start){assert(++c->base.starts[action]==1);}else assert(c->base.starts[action]==1);
 struct mrs_session *s=action==MS_SET_TIME?&c->time:&c->buffer;
 if(action==MS_SET_TIME&&c->precheck<2){
  uint32_t v;uint32_t address=c->precheck==0?MM_RX_ERROR:MM_RX_PRESENT;
  if(mm_read(c->base.m,address,&v)||v)return -1;
  c->precheck++;return 0;
 }
 if(!s->started&&mrs_begin(s,c->base.rt,action==MS_SET_TIME?MRS_TIME:MRS_BUFFER,1))return -1;
 return mrs_step(s);
}
int master_resumable_composition_test(const uint8_t *frames,size_t length){
 assert(length==40);const unsigned modes[8]={0,1,2,3,4,5,9,12};unsigned cases=0,maximum_rt_ops=0;
 for(unsigned n=0;n<69;n++){
  struct mfo_gate gate;mfo_init(&gate);assert(!mfo_fresh_epoch(&gate,1,15)&&!mfo_request_master(&gate)&&!mfo_grant_master(&gate,7));
  struct mfs_session session={0};assert(!mfs_open(&session,&gate,gate.ticket,n==68?3:32,3));
  struct resumable_actions actions={0};
  struct resumable_fixture f={.fake={.frames=frames,.mode=n<8?modes[n]:0,.failed_route_stage=127},.session=&session,.actions=&actions};
  if(n>=8&&n<68){unsigned index=(n-8)%30;f.injected_action=index<10?MS_SET_TIME:MS_BUFFER;f.injected_ordinal=index<10?index+1:index-9;f.cancel=n>=38;}
  struct mm_bus bus={&f,resumable_read,resumable_write,resumable_fence};struct mm_transport mm;assert(!mm_bind(&mm,&bus,3,1));
  struct mrt_setup rt={.mm=&mm};struct ma_slot_state slot={0};struct mq_transport queue={.rx={&mm,mm_acquire,mm_release},.ctx=&mm,.pending=mm_pending,.send=mm_send};
  actions.base=(struct action_context){.m=&mm,.rt=&rt,.slot=&slot};struct msc_io io={&actions,resumable_action,{&queue,mq_send_checked,mq_recv_slot}};
  int result=0;unsigned turns=0,management=0;
  while(!result){
   management++;assert(mfo_worker_dispatch(&gate)==MFO_BUSY);unsigned before=f.fake.calls;enum ms_action prior=session.setup.plan.action;
   result=mfs_step(&session,&io);assert(++turns<1200);
   if(prior==MS_SET_TIME||prior==MS_BUFFER){unsigned ops=f.fake.calls-before;assert(ops<=1);if(ops>maximum_rt_ops)maximum_rt_ops=ops;}
  }
  assert(management==turns&&mfo_worker_dispatch(&gate)==MFO_BUSY);
  if(n==0||n==7){assert(result==1&&gate.state==MFO_HELD&&turns==(n==0?550u:552u)&&f.fake.tx==259&&f.fake.pops==260&&rt.credits==16);}
  else {assert(result<0&&gate.state==MFO_FAULT&&!rt.credits);if(n>=8&&n<68)assert(f.action_ops==f.injected_ordinal);}
  if(n>=38&&n<68)assert(result==MFO_CANCELLED);
  if(n==68)assert(f.fake.time==0&&f.fake.tx==1&&!rt.time_attempted); /* Budget too short: fail before time write. */
  unsigned calls=f.fake.calls,callbacks=actions.base.calls;
  assert(mfs_step(&session,&io)==result&&f.fake.calls==calls&&actions.base.calls==callbacks);
  cases++;
 }
 assert(maximum_rt_ops==1);
 printf("MASTER_RESUMABLE_COMPOSITION_PASS cases=%u healthy_turns=550 max_rt_callbacks=1\n",cases);return 0;
}
