/* SPDX-License-Identifier: LGPL-3.0-or-later */
/* Test-only canonical full-star setup composition; not production master service. */
#ifdef MASTER_A53_EMULATION
extern void master_emulation_assert(int);
extern void master_emulation_setup_cooperative_pass(unsigned);
#define assert(condition) master_emulation_assert(!!(condition))
#else
#include <assert.h>
#include <stdio.h>
#endif
#include "master_control_codec.h"
#include "master_setup_sequence.h"
#include "master_rt_setup.h"
#include "master_route_queue.h"
#include "master_star_setup.h"
#include "master_setup_cooperative.h"
#include "master_setup_mock_fixture.h"
/* Synchronous cancellation from the sole owner's backend callback must win
 * over pending/success/error, including the last routing ACK. No MMIO here. */
struct cancel_context {struct msc_setup *session;unsigned calls;int result;};
static int cancel_action(void *ctx,enum ms_action action,unsigned start){
 struct cancel_context *c=ctx;(void)action;(void)start;c->calls++;
 msc_cancel(c->session);return c->result;
}
static int cancel_send(void *ctx,const uint8_t *bytes,size_t length){
 struct cancel_context *c=ctx;assert(bytes&&length);c->calls++;
 msc_cancel(c->session);return c->result;
}
static int cancel_recv(void *ctx,uint32_t *kind){
 struct cancel_context *c=ctx;c->calls++;*kind=0x32;
 msc_cancel(c->session);return c->result;
}
static void cancellation_callback_test(void){
 for(unsigned phase=0;phase<3;phase++)for(int result=-1;result<=1;result++){
  struct msc_setup session;assert(msc_init_epoch(&session,3,3,1)==0);
  struct cancel_context context={&session,0,result};
  struct msc_io io={&context,cancel_action,{&context,cancel_send,cancel_recv}};
  if(phase){session.plan.action=MS_ROUTING;}
  if(phase==2){session.route.completed=256;session.route.send_attempts=257;
   assert(mt_begin(&session.route.tx,0x31,3)==0);
   assert(mt_tx_complete(&session.route.tx,1)==0);
  }
  assert(msc_step(&session,&io)==-100&&context.calls==1);
  assert(session.plan.action==MS_FAILED&&session.plan.error==-100);
  assert(session.route.completed==(phase==2?256u:0u));
  unsigned attempts=session.route.send_attempts;
  assert(msc_step(&session,&io)==-100&&context.calls==1);
  msc_cancel(&session);assert(msc_step(&session,&io)==-100&&context.calls==1);
  assert(session.route.send_attempts==attempts);
 }
 struct msi_table route;assert(msi_init_epoch(&route,3,1)==0);
 assert(msi_fail(&route,MT_TIMEOUT)==MT_TIMEOUT);msi_cancel(&route);
 assert(route.terminal==MT_TIMEOUT);
}
int master_setup_cooperative_test(const uint8_t *frames,size_t length){
 cancellation_callback_test();
 assert(length==40);const unsigned cuts[4]={0,127,255,256};unsigned maximum=0;
 for(unsigned case_id=0;case_id<22;case_id++){
  unsigned mode=case_id<8?case_id:case_id<16?8+(case_id-8)/4:case_id==16?10:case_id==21?12:11;
  unsigned cut=case_id<8||case_id==16||case_id==21?0:cuts[case_id<16?(case_id-8)%4:case_id-17];
  struct setup_fake f={.frames=frames,.mode=mode,.failed_route_stage=cut};struct mm_bus bus={&f,setup_read,setup_write,setup_fence};struct mm_transport m;assert(mm_bind(&m,&bus,3,1)==0);
  struct mrt_setup rt={.mm=&m};struct ma_slot_state slot={0};struct mq_transport queue={.rx={&m,mm_acquire,mm_release},.ctx=&m,.pending=mm_pending,.send=mm_send};
  struct action_context context={.m=&m,.rt=&rt,.slot=&slot};struct msc_io io={&context,action_step,{&queue,mq_send_checked,mq_recv_slot}};struct msc_setup session;assert(msc_init_epoch(&session,3,3,1)==0);
  unsigned steps=0,management=0;int result=0;
  while(!result){
   management++;unsigned before=f.calls,action_calls=context.calls;
   result=msc_step(&session,&io);steps++;assert(context.calls-action_calls<=1);if(f.calls-before>maximum)maximum=f.calls-before;
   if((mode==10&&f.tx==1&&!f.pops)||(mode==11&&session.plan.action==MS_ROUTING&&session.route.tx.state==MT_WAIT&&f.tx==cut+2)){msc_cancel(&session);result=msc_step(&session,&io);}
   assert(steps<=1100);
  }
  assert(management==steps);
#ifdef FORCE_COOPERATIVE_TURNS_ASSERT
  if(!mode)assert(steps==521);
#endif
  if(!mode||mode==12){assert(result==1&&steps==(mode==12?524u:522u)&&f.tx==259&&f.pops==260&&rt.credits==16);for(unsigned a=MS_LINK;a<=MS_BUFFER;a++)if(a!=MS_ROUTING)assert(context.starts[a]==1);}
  else assert(result<0&&session.plan.action==MS_FAILED);
  if(mode==1||mode==7)assert(f.time==0&&f.tx==1);
  if(mode==2||mode==3)assert(f.time==1&&f.tx==1&&f.requests==0);
  if(mode==4)assert(f.tx==259&&f.requests==0);
  if(mode==8||mode==9)assert(f.tx==cut+2&&f.requests==0&&session.route.completed==cut);
  if(mode==10)assert(f.tx==1&&f.pops==0&&f.present==1);
  if(mode==11)assert(f.tx==cut+2&&f.pops==cut+2&&f.present==1&&session.route.tx.commit_attempted==1);
  if(result<0){int saved=session.plan.error;msc_cancel(&session);assert(session.plan.error==saved);}
  unsigned calls=f.calls,actions=context.calls;assert(msc_step(&session,&io)==result&&f.calls==calls&&context.calls==actions);
 }
#ifdef MASTER_A53_EMULATION
 master_emulation_setup_cooperative_pass(maximum);
#else
 printf("MASTER_SETUP_COOPERATIVE_PASS cases=22 healthy_turns=522 max_mock_ops_per_turn=%u\n",maximum);
#endif
 return 0;
}
