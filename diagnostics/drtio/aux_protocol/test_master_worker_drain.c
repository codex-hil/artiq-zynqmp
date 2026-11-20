/* SPDX-License-Identifier: LGPL-3.0-or-later */
#include <assert.h>
#include <stdio.h>
#include "master_worker_progress.h"
#include "master_foreground_setup.h"
#include "master_setup_mock_fixture.h"
struct drain_fixture {struct setup_fake fake;struct mfs_session *session;};
static int drain_read(void *ctx,uint32_t a,uint32_t *v){struct drain_fixture *f=ctx;assert(mfs_authorized(f->session));return setup_read(&f->fake,a,v);}
static int drain_write(void *ctx,uint32_t a,uint32_t v){struct drain_fixture *f=ctx;assert(mfs_authorized(f->session));return setup_write(&f->fake,a,v);}
static int drain_fence(void *ctx){struct drain_fixture *f=ctx;assert(mfs_authorized(f->session));return setup_fence(&f->fake);}
int master_worker_drain_test(const uint8_t *frames,size_t length){
 assert(length==40);unsigned completed=0,blocked=0,publication_attempts=0;
 for(unsigned scenario=0;scenario<8;scenario++){
  struct mfo_gate gate;mfo_init(&gate);assert(!mfo_fresh_epoch(&gate,1,15)&&!mwp_new_work(&gate,2));
  uint64_t worker=gate.ticket;assert(!mfo_request_master(&gate));
  struct mwp_reply reply={0};struct mfs_session session={0};
  struct drain_fixture fixture={.fake={.frames=frames},.session=&session};
  struct mm_bus bus={&fixture,drain_read,drain_write,drain_fence};struct mm_transport mm;
  /* The first event is async RPC, synchronous reply or host RPC exception. */
  enum mwp_phase phase=scenario==0?MWP_ASYNC_REPLY:MWP_SYNC_REPLY;
  unsigned command=scenario==0?3:scenario==2?7:4;
  assert(mfo_grant_master(&gate,7)==MFO_BUSY&&mwp_new_work(&gate,1)==MFO_BUSY);
  assert(mfs_open(&session,&gate,worker,3,3)==MFO_INVALID&&fixture.fake.calls==0);
  if(scenario==3){ /* Missing RPC event: no fabricated progress/quiescence. */
   assert(mwp_progress_once(&reply,&gate,command)==MFO_INVALID);
  }else if(scenario==5){
   assert(mwp_arm(&reply,&gate,worker+1,1,1,phase,1)==MFO_INVALID);
  }else{
   assert(!mwp_arm(&reply,&gate,worker,1,1,phase,1));
   if(scenario==6){
    assert(mwp_abandon(&gate,worker,1,-66)==-66);
    assert(mwp_progress_once(&reply,&gate,command)==MFO_INVALID);
   }else{
    assert(!mwp_progress_once(&reply,&gate,command));publication_attempts++;
    if(scenario==4)assert(mwp_abandon(&gate,worker,1,-44)==-44); /* Ambiguous failed publication. */
    assert(mwp_progress_once(&reply,&gate,command)==MFO_INVALID);
    if(scenario==1||scenario==2||scenario==7){
     assert(!mwp_arm(&reply,&gate,worker,1,2,MWP_EXCEPTION_ACK,1));
     assert(!mwp_progress_once(&reply,&gate,6));publication_attempts++;
    }
   }
  }
  assert(fixture.fake.calls==0&&mfo_grant_master(&gate,7)==MFO_BUSY);
  assert(mwp_new_work(&gate,2)==MFO_BUSY&&gate.ticket==worker);
  if(scenario>=3){
   /* Missing READY/quiescence (7), bad/missing event, failed publication or
    * cancellation cannot proceed to target bind. */
   assert(mfo_worker_quiesced(&gate,worker,0)==MFO_INVALID);
   assert(mfs_open(&session,&gate,worker,3,3)==MFO_INVALID&&fixture.fake.calls==0);
   assert(gate.state==(scenario==4||scenario==6?MFO_FAULT:MFO_DRAINING));
   blocked++;continue;
  }
  /* This explicit receipt represents externally established quiescence.
   * It is NOT inferred from command3/4/6/7 success or a software busy snapshot. */
  assert(mfo_worker_quiesced(&gate,worker,0)==MFO_INVALID);
  assert(!mfo_worker_quiesced(&gate,worker,1)&&!mfo_grant_master(&gate,7));
  assert(!mfs_open(&session,&gate,gate.ticket,3,3)&&!mm_bind(&mm,&bus,3,1));
  struct mrt_setup rt={.mm=&mm};struct ma_slot_state slot={0};
  struct mq_transport queue={.rx={&mm,mm_acquire,mm_release},.ctx=&mm,.pending=mm_pending,.send=mm_send};
  struct action_context context={.m=&mm,.rt=&rt,.slot=&slot};struct msc_io io={&context,action_step,{&queue,mq_send_checked,mq_recv_slot}};
  unsigned turns=0,network_turns=0;int result=0;
  while(!result){network_turns++;assert(mwp_new_work(&gate,2)==MFO_BUSY);result=mfs_step(&session,&io);assert(++turns<=522);}
  assert(result==1&&turns==522&&network_turns==turns&&gate.state==MFO_HELD);
  assert(fixture.fake.tx==259&&fixture.fake.pops==260&&rt.credits==16);
  unsigned calls=fixture.fake.calls;
  assert(mwp_progress_once(&reply,&gate,command)==MFO_INVALID&&fixture.fake.calls==calls);
  assert(!mfo_release_master(&gate,gate.ticket,7)&&!mwp_new_work(&gate,1));completed++;
 }
 assert(completed==3&&blocked==5&&publication_attempts==8);
 printf("MASTER_WORKER_DRAIN_PASS streams=8 setup_complete=3 no_target_io=5 publication_attempts=8\n");return 0;
}
