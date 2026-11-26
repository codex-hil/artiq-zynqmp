/* SPDX-License-Identifier: LGPL-3.0-or-later */
#ifdef MASTER_A53_EMULATION
extern void master_emulation_assert(int);
extern void master_emulation_network_static_pass(void);
#define assert(condition) master_emulation_assert(!!(condition))
#else
#include <assert.h>
#include <stdio.h>
#endif
#include "master_network_static.h"
#include "master_network_fault_observer.h"
#include "master_setup_mock_fixture.h"
struct fixture {struct setup_fake fake;struct mfo_gate *gate;struct mnf_latch latch;struct mnf_view view;unsigned probing,probes,observations;};
static void probe(struct fixture *f){
 assert(!f->probing);f->probing=1;unsigned calls=f->fake.calls;
 struct mnh_status out={17,18,19};
 assert(mns_begin(0,0,0,0,0,0,0,0,0)==MFO_BUSY&&mns_poll()==MFO_BUSY&&mns_snapshot(&out)==MFO_BUSY&&out.complete==17&&out.credits==18&&out.error==19);
 assert(f->fake.calls==calls);f->probing=0;f->probes+=3;
}
static int rd(void *ctx,uint32_t a,uint32_t *v){struct fixture *f=ctx;probe(f);return setup_read(&f->fake,a,v);}
static int wr(void *ctx,uint32_t a,uint32_t v){struct fixture *f=ctx;probe(f);return setup_write(&f->fake,a,v);}
static int fence(void *ctx){struct fixture *f=ctx;probe(f);return setup_fence(&f->fake);}
static int health(void *ctx,struct mnh_health *out){struct fixture *f=ctx;probe(f);f->observations++;return mnf_observe(&f->view,out);}
int master_network_static_test(const uint8_t *frames,size_t length){
 (void)action_step;assert(length==40);
 static struct mfo_gate gate;static struct fixture f={.latch=MNF_LATCH_INITIALIZER};
 struct mnh_status out={17,18,19};assert(mns_poll()==MNH_INVALID&&mns_snapshot(&out)==MNH_INVALID&&out.complete==17);
 mfo_init(&gate);assert(!mfo_fresh_epoch(&gate,1,15)&&!mfo_request_master(&gate)&&!mfo_grant_master(&gate,7));
 f.fake.frames=frames;f.gate=&gate;f.view=(struct mnf_view){&f.latch,9,7};struct mm_bus bus={&f,rd,wr,fence};
 assert(!mns_begin(&gate,gate.ticket,&bus,&f,health,3,64,8730,8827)&&!f.fake.calls);
 unsigned observations=f.observations;assert(mns_begin(&gate,gate.ticket,&bus,&f,health,3,64,8730,8827)==MNH_INVALID&&f.observations==observations);
 int result=0;unsigned turns=0;
 while(!result){unsigned before=f.fake.calls;assert(!mns_snapshot(&out)&&!out.complete&&!out.credits);result=mns_poll();assert(f.fake.calls-before<=1&&++turns<=8830);}
 assert(result==1&&turns==8830&&f.fake.tx==259&&f.fake.pops==260&&gate.state==MFO_HELD);
 assert(!mns_snapshot(&out)&&out.complete&&out.credits==16&&!out.error);
 unsigned calls=f.fake.calls;mnf_publish(&f.latch);
 assert(mns_snapshot(&out)==MNE_UNSAFE&&!out.complete&&!out.credits&&gate.state==MFO_FAULT&&gate.owner==MFO_MASTER_OWNER&&f.fake.calls==calls);
#ifdef FORCE_NETWORK_STATIC_ASSERT
 assert(out.complete==1); /* Deliberately false: fresh publication withdrew success. */
#endif
 assert(mnf_seen(&f.latch));assert(mns_poll()==MNE_UNSAFE&&mns_snapshot(&out)==MNE_UNSAFE&&!out.complete&&f.fake.calls==calls);
 assert(f.probes==3*(f.fake.calls+f.observations));
 assert(!mfo_fresh_epoch(&gate,2,15)&&!mfo_request_master(&gate)&&!mfo_grant_master(&gate,7));uint64_t ticket=gate.ticket;
 assert(mns_begin(&gate,ticket,&bus,&f,health,3,64,8730,8827)==MNH_INVALID&&mns_poll()==MNE_UNSAFE&&mns_snapshot(&out)==MNE_UNSAFE&&!out.complete&&gate.ticket==ticket&&gate.state==MFO_MASTER&&f.fake.calls==calls);
#ifdef MASTER_A53_EMULATION
 master_emulation_network_static_pass();
#else
 printf("MASTER_NETWORK_STATIC_PASS turns=8830 max_callbacks=1 single_use=1\n");
#endif
 return 0;
}
