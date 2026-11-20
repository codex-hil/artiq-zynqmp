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
struct setup_fake {const uint8_t *frames;unsigned mode,calls,tx,time,requests,pops,failed_route_stage,deferred_reads;uint32_t present,pointer,length,force,count;uint8_t txbytes[40];const uint8_t *reply;};
static void enqueue(struct setup_fake *f,unsigned frame){assert(!f->present);f->reply=f->frames+frame*8;f->present=1;}
static int setup_read(void *ctx,uint32_t a,uint32_t *v){
 struct setup_fake *f=ctx;f->calls++;
 if(a==0xa0000800)*v=0x47534d31;else if(a==0xa0000804)*v=3;else if(a==0xa0000808)*v=125000000;
 else if(a==MRT_RX_UP)*v=f->mode==6?0:1;
 else if(a==MRT_ERROR)*v=f->mode==5&&f->requests?4:0;
 else if(a==MRT_SET_TIME||a==MRT_WAIT||a==MM_TX_BUSY||a==MM_RX_ERROR)*v=0;
 else if(a==MRT_FORCE)*v=f->force;else if(a==MRT_COUNT)*v=f->count;else if(a==MRT_SPACE)*v=16;
 else if(a==MM_RX_PRESENT){*v=f->present;if(f->mode==12&&f->time==1&&f->tx==1&&f->pops==1&&f->deferred_reads++<2)*v=0;}else if(a==MM_RX_POINTER)*v=f->pointer;else if(a==MM_TX_LENGTH)*v=f->length;
 else {assert(f->present&&f->reply);unsigned k=a-(MM_RX_MEMORY+f->pointer*1024);assert(k==0||k==4);*v=(uint32_t)f->reply[k]|((uint32_t)f->reply[k+1]<<8)|((uint32_t)f->reply[k+2]<<16)|((uint32_t)f->reply[k+3]<<24);
  if(f->mode==9&&f->tx>=2&&f->tx<=258&&f->tx-2==f->failed_route_stage&&k==4)*v^=0x1000000;
 }
 return 0;
}
static int setup_write(void *ctx,uint32_t a,uint32_t v){
 struct setup_fake *f=ctx;f->calls++;
 if(a==MM_TX_LENGTH)f->length=v;
 else if(a==MM_TX_BUSY){
  assert(f->tx<259);
  unsigned kind=f->tx==0?0:f->tx<=256?0x30:f->tx==257?0x31:0x20;
  assert(f->txbytes[0]==kind&&f->length==(kind==0x30?40u:8u));
  if(kind==0x30){unsigned destination=f->tx-1;assert(f->txbytes[1]==destination);
   for(unsigned i=0;i<32;i++){unsigned value=0xff;if(destination==0&&i==0)value=0;if(destination==1&&i==0)value=1;if(destination==1&&i==1)value=0;assert(f->txbytes[2+i]==value);}
  }
  if(f->tx==0)enqueue(f,f->mode==7?1:0);
  else if(f->tx<=257){if(f->mode!=8||f->tx-1!=f->failed_route_stage)enqueue(f,2);}
  else enqueue(f,f->mode==4?4:3);
  f->tx++;
 }else if(a==MM_RX_PRESENT){assert(v==1&&f->present);f->present=0;f->pointer=(f->pointer+1)%8;f->pops++;if(f->mode==1&&f->pops==1)enqueue(f,1);}
 else if(a==MRT_SET_TIME){assert(v==1&&!f->present);f->time++;if(f->mode!=2)enqueue(f,f->mode==3?0:1);}
 else if(a==MRT_DEST)assert(v==1);else if(a==MRT_FORCE)f->force=v;
 else if(a==MRT_BUFFER){assert(v==1&&f->force);f->requests++;f->count++;}
 else {assert(a>=MM_TX_MEMORY&&a<MM_TX_MEMORY+40);unsigned i=a-MM_TX_MEMORY;for(unsigned j=0;j<4;j++)f->txbytes[i+j]=(uint8_t)(v>>(8*j));}
 return 0;
}
static int setup_fence(void *ctx){((struct setup_fake *)ctx)->calls++;return 0;}
static int control_reply(struct mm_transport *m,struct ma_slot_state *s,uint32_t expected){
 struct ma_slot_io io={m,mm_acquire,mm_release};uint32_t kind=0;
 int r=ma_receive_fixed(s,&io,&kind,aux_master_control_decode);
 if(r<=0)return r;
 return kind==expected?1:-1;
}

struct action_context {struct mm_transport *m;struct mrt_setup *rt;struct ma_slot_state *slot;unsigned starts[8],calls;};
static int action_step(void *ctx,enum ms_action action,unsigned start){
 struct action_context *c=ctx;c->calls++;assert(action>=MS_LINK&&action<=MS_BUFFER&&action!=MS_ROUTING);
 if(start){c->starts[action]++;assert(c->starts[action]==1);}else assert(c->starts[action]==1);
 switch(action){
 case MS_LINK:assert(start);return mrt_live(c->m)?-1:1;
 case MS_SET_TIME:assert(start);return mm_pending(c->m)==0&&!mrt_set_time_once(c->rt)?1:-1;
 case MS_BUFFER:assert(start);return mrt_buffer_once(c->rt)?-1:1;
 case MS_TSC_ACK:return control_reply(c->m,c->slot,4);
 case MS_ECHO:case MS_STATUS:
  if(start){uint8_t bytes[8];int n=aux_master_control_encode(action==MS_ECHO?0:0x20,action==MS_ECHO?0:1,bytes,sizeof(bytes));return n==8&&!mm_send(c->m,bytes,8)?0:-1;}
  return control_reply(c->m,c->slot,action==MS_ECHO?1:0x22);
 default:assert(0);return -1;
 }
}
int master_setup_cooperative_test(const uint8_t *frames,size_t length){
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
