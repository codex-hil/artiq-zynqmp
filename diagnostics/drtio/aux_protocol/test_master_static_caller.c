/* SPDX-License-Identifier: LGPL-3.0-or-later */
#ifdef MASTER_A53_EMULATION
extern void master_emulation_assert(int);
extern void master_emulation_static_caller_pass(void);
#define assert(condition) master_emulation_assert(!!(condition))
#else
#include <assert.h>
#include <stdio.h>
#endif
#include "master_static_caller.h"
#include "master_setup_mock_fixture.h"
struct fixture {struct setup_fake fake;struct mfo_gate *gate;};
static int read_reg(void *ctx,uint32_t a,uint32_t *v){struct fixture *f=ctx;assert(f->gate->state==MFO_MASTER);return setup_read(&f->fake,a,v);}
static int write_reg(void *ctx,uint32_t a,uint32_t v){struct fixture *f=ctx;assert(f->gate->state==MFO_MASTER);return setup_write(&f->fake,a,v);}
static int fence(void *ctx){struct fixture *f=ctx;assert(f->gate->state==MFO_MASTER);return setup_fence(&f->fake);}
int master_static_caller_test(const uint8_t *frames,size_t length){
 (void)action_step;assert(length==40);
 /* Owner/bus context persist after this test returns; singleton never reset. */
 static struct mfo_gate gate;static struct fixture f;
 f=(struct fixture){.fake={.frames=frames},.gate=&gate};struct mm_bus bus={&f,read_reg,write_reg,fence};struct mfc_status status;
 assert(mfc_poll()==MFG_INVALID&&mfc_cancel()==MFG_INVALID&&!mfc_snapshot(&status)&&!status.initialized&&status.result==MFG_INVALID&&!f.fake.calls);
 assert(mfc_begin(&gate,1,&bus,3,64,8730,8827)==MMB_INVALID&&!f.fake.calls);
 mfo_init(&gate);assert(!mfo_fresh_epoch(&gate,1,15)&&!mfo_request_master(&gate)&&!mfo_grant_master(&gate,7));
 assert(!mfc_begin(&gate,gate.ticket,&bus,3,64,8730,8827)&&!f.fake.calls);
 assert(mfc_begin(&gate,gate.ticket,&bus,3,64,8730,8827)==MFO_BUSY&&!f.fake.calls);
 unsigned turns=0,network_turns=0;int result=0;
 while(!result){
  network_turns++;unsigned before=f.fake.calls;assert(!mfc_snapshot(&status)&&status.initialized&&!status.candidate_complete&&!status.credits&&status.result==0&&f.fake.calls==before);
  assert(mfo_worker_dispatch(&gate)==MFO_BUSY);result=mfc_poll();assert(f.fake.calls-before<=1&&++turns<=8830);
 }
#ifdef FORCE_STATIC_CALLER_ASSERT
 assert(turns==8829); /* Deliberately false: healthy uses8830. */
#endif
 assert(result==1&&turns==8830&&network_turns==turns&&f.fake.tx==259&&f.fake.pops==260&&gate.state==MFO_HELD);
 unsigned calls=f.fake.calls;assert(!mfc_snapshot(&status)&&status.candidate_complete&&status.result==1&&status.credits==16&&status.routing_completed==257&&f.fake.calls==calls);
 gate.setup_ticket=0;assert(!mfc_snapshot(&status)&&!status.candidate_complete&&!status.credits&&status.result==MFG_INVALID&&f.fake.calls==calls);
 assert(mfc_poll()==MFG_INVALID&&gate.state==MFO_FAULT&&mfc_cancel()==MFG_INVALID&&f.fake.calls==calls);
 assert(!mfo_fresh_epoch(&gate,2,15)&&!mfo_request_master(&gate)&&!mfo_grant_master(&gate,7));
 assert(mfc_begin(&gate,gate.ticket,&bus,3,64,8730,8827)==MFO_BUSY&&gate.state==MFO_MASTER&&mfc_poll()==MFG_INVALID&&f.fake.calls==calls);
#ifdef MASTER_A53_EMULATION
 master_emulation_static_caller_pass();
#else
 printf("MASTER_STATIC_CALLER_PASS healthy_turns=8830 max_callbacks_per_turn=1 single_use=1\n");
#endif
 return 0;
}
