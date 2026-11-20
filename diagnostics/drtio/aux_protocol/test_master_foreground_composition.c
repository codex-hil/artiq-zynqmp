/* SPDX-License-Identifier: LGPL-3.0-or-later */
#ifdef MASTER_A53_EMULATION
extern void master_emulation_assert(int);
extern void master_emulation_foreground_pass(unsigned);
#define assert(condition) master_emulation_assert(!!(condition))
#else
#include <assert.h>
#include <stdio.h>
#endif
#include "master_foreground_setup.h"
#include "master_setup_mock_fixture.h"
struct guarded_fixture {struct setup_fake fake;struct mfs_session *session;};
static int guarded_read(void *ctx,uint32_t a,uint32_t *v){
 struct guarded_fixture *f=ctx;assert(mfs_authorized(f->session));return setup_read(&f->fake,a,v);
}
static int guarded_write(void *ctx,uint32_t a,uint32_t v){
 struct guarded_fixture *f=ctx;assert(mfs_authorized(f->session));return setup_write(&f->fake,a,v);
}
static int guarded_fence(void *ctx){struct guarded_fixture *f=ctx;assert(mfs_authorized(f->session));return setup_fence(&f->fake);}
int master_foreground_composition_test(const uint8_t *frames,size_t length){
 assert(length==40);unsigned cases=0;
 /* Healthy, native failures, cancellation after first/late TX, independent
  * ownership revocation before a turn. Actual Rust codec + shared MMIO fixture. */
 const unsigned modes[8]={0,3,5,8,9,10,11,0};
 for(unsigned n=0;n<8;n++){
  struct mfo_gate gate;mfo_init(&gate);struct mfs_session session={0};
  struct guarded_fixture fixture={.fake={.frames=frames,.mode=modes[n],.failed_route_stage=127},.session=&session};
  struct setup_fake *f=&fixture.fake;
  struct mm_bus bus={&fixture,guarded_read,guarded_write,guarded_fence};struct mm_transport mm;
  struct mrt_setup rt={.mm=&mm};struct ma_slot_state slot={0};
  struct mq_transport queue={.rx={&mm,mm_acquire,mm_release},.ctx=&mm,.pending=mm_pending,.send=mm_send};
  struct action_context context={.m=&mm,.rt=&rt,.slot=&slot};struct msc_io io={&context,action_step,{&queue,mq_send_checked,mq_recv_slot}};
  assert(mfs_open(&session,&gate,1,3,3)==MFO_INVALID&&f->calls==0);
  assert(!mfo_fresh_epoch(&gate,1,15)&&!mfo_worker_dispatch(&gate));uint64_t worker=gate.ticket;
  assert(!mfo_request_master(&gate)&&mfo_grant_master(&gate,7)==MFO_BUSY);
  assert(mfs_open(&session,&gate,worker,3,3)==MFO_INVALID&&f->calls==0);
  assert(mfo_worker_dispatch(&gate)==MFO_BUSY);
  assert(!mfo_worker_quiesced(&gate,worker,1)&&!mfo_grant_master(&gate,7));
  assert(!mfs_open(&session,&gate,gate.ticket,3,3)&&mfs_authorized(&session));
  struct mfs_session replay={0};assert(mfs_open(&replay,&gate,gate.ticket,3,3)==MFO_BUSY&&!replay.initialized);
  assert(!mm_bind(&mm,&bus,3,1)); /* Bind itself performs reads, AFTER grant. */
  unsigned turns=0,management=0;int result=0;
  while(!result){
   management++;assert(mfo_worker_dispatch(&gate)==MFO_BUSY);
   if((n==5&&f->tx==1&&!f->pops)||(n==6&&f->tx==129&&session.setup.route.tx.state==MT_WAIT))assert(mfs_cancel(&session)==MFO_CANCELLED);
   if(n==7&&f->tx==1)assert(mfo_fault(&gate,-88)==-88);
   result=mfs_step(&session,&io);assert(++turns<1100);
  }
  assert(management==turns&&mfo_worker_dispatch(&gate)==MFO_BUSY);
  unsigned calls=f->calls,actions=context.calls;
  assert(mfs_step(&session,&io)==result&&f->calls==calls&&context.calls==actions);
  if(n==0){
#ifdef FORCE_FOREGROUND_ASSERT
   assert(gate.state==MFO_IDLE); /* Deliberately false: success must retain ownership. */
#endif
   assert(result==1&&gate.state==MFO_HELD&&f->tx==259&&f->pops==260&&turns==522);
   assert(!mfs_authorized(&session)&&mfo_release_master(&gate,gate.ticket,0)==MFO_INVALID);
   assert(!mfo_release_master(&gate,gate.ticket,7)&&!mfo_worker_dispatch(&gate));
   assert(mfs_step(&session,&io)==MFO_INVALID&&f->calls==calls&&gate.state==MFO_WORKER);
  }else{
   assert(result<0&&gate.state==MFO_FAULT);
   assert(mfo_release_master(&gate,gate.ticket,7)==MFO_BUSY);
   uint64_t old=session.ticket;assert(!mfo_fresh_epoch(&gate,2,15));
   assert(!mfo_request_master(&gate)&&!mfo_grant_master(&gate,7)&&gate.ticket>old);
   assert(mfs_step(&session,&io)==MFO_INVALID&&f->calls==calls&&gate.state==MFO_MASTER);
   assert(mfs_cancel(&session)==MFO_INVALID&&gate.state==MFO_MASTER);
  }
  cases++;
 }
#ifdef MASTER_A53_EMULATION
 master_emulation_foreground_pass(cases);
#else
 printf("MASTER_FOREGROUND_COMPOSITION_PASS cases=%u healthy_turns=522\n",cases);
#endif
 return 0;
}
