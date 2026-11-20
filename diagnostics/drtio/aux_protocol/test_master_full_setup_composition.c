/* SPDX-License-Identifier: LGPL-3.0-or-later */
/* Test-only canonical full-star setup composition; not production master service. */
#ifdef MASTER_A53_EMULATION
extern void master_emulation_assert(int);
extern void master_emulation_full_setup_pass(void);
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
struct setup_fake {const uint8_t *frames;unsigned mode,calls,tx,time,requests,pops,failed_route_stage;uint32_t present,pointer,length,force,count;uint8_t txbytes[40];const uint8_t *reply;};
static void enqueue(struct setup_fake *f,unsigned frame){assert(!f->present);f->reply=f->frames+frame*8;f->present=1;}
static int setup_read(void *ctx,uint32_t a,uint32_t *v){
 struct setup_fake *f=ctx;f->calls++;
 if(a==0xa0000800)*v=0x47534d31;else if(a==0xa0000804)*v=3;else if(a==0xa0000808)*v=125000000;
 else if(a==MRT_RX_UP)*v=f->mode==6?0:1;
 else if(a==MRT_ERROR)*v=f->mode==5&&f->requests?4:0;
 else if(a==MRT_SET_TIME||a==MRT_WAIT||a==MM_TX_BUSY||a==MM_RX_ERROR)*v=0;
 else if(a==MRT_FORCE)*v=f->force;else if(a==MRT_COUNT)*v=f->count;else if(a==MRT_SPACE)*v=16;
 else if(a==MM_RX_PRESENT)*v=f->present;else if(a==MM_RX_POINTER)*v=f->pointer;else if(a==MM_TX_LENGTH)*v=f->length;
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
 struct ma_slot_io io={m,mm_acquire,mm_release};
 for(unsigned i=0;i<3;i++){uint32_t kind=0;int r=ma_receive_fixed(s,&io,&kind,aux_master_control_decode);if(r<0)return -1;if(r==1)return kind==expected?0:-1;}
 return -1;
}
static int control_exchange(struct mm_transport *m,struct ma_slot_state *s,uint32_t request,uint32_t value,uint32_t expected){
 uint8_t bytes[8];int n=aux_master_control_encode(request,value,bytes,sizeof(bytes));
 if(n!=8||mm_send(m,bytes,8))return -1;
 return control_reply(m,s,expected);
}
int master_full_setup_composition_test(const uint8_t *frames,size_t length){
 assert(length==40);
 const unsigned cuts[4]={0,127,255,256};
 for(unsigned case_id=0;case_id<16;case_id++){
  unsigned mode=case_id<8?case_id:8+(case_id-8)/4;
  unsigned cut=case_id<8?0:cuts[(case_id-8)%4];
  struct setup_fake f={.frames=frames,.mode=mode,.failed_route_stage=cut};struct mm_bus bus={&f,setup_read,setup_write,setup_fence};struct mm_transport m;
  assert(mm_bind(&m,&bus,3,1)==0);struct mrt_setup rt={.mm=&m};struct ma_slot_state slot={0};
  struct mq_transport queue={.rx={&m,mm_acquire,mm_release},.ctx=&m,.pending=mm_pending,.send=mm_send};struct mst_table route;mst_init_epoch(&route);
  struct ms_setup plan;assert(ms_init_epoch(&plan,3,1)==0);
  for(unsigned action=MS_LINK;action<=MS_BUFFER;action++){
   assert(ms_claim(&plan)==(int)action);int result=-1;
   switch(action){
    case MS_LINK:result=mrt_live(&m);break;
    case MS_ECHO:result=control_exchange(&m,&slot,0,0,1);break;
    case MS_SET_TIME:result=mm_pending(&m)==0?mrt_set_time_once(&rt):-1;break;
    case MS_TSC_ACK:result=control_reply(&m,&slot,4);break;
    case MS_ROUTING:{struct mr_io io={&queue,mq_send_checked,mq_recv_slot};result=mst_run_once(&route,&io,3);break;}
    case MS_STATUS:result=control_exchange(&m,&slot,0x20,1,0x22);break;
    case MS_BUFFER:result=mrt_buffer_once(&rt);break;
    default:assert(0);
   }
   if(result){assert(ms_result(&plan,-9)==-9);break;}assert(ms_result(&plan,1)==0);
  }
#ifdef FORCE_FULL_SETUP_ASSERT
  if(!mode)assert(f.tx==258); /* Deliberately false emulator negative only. */
#endif
  if(!mode){assert(plan.action==MS_COMPLETE&&f.tx==259&&f.time==1&&f.requests==1&&f.pops==260&&rt.credits==16);}
  else assert(plan.action==MS_FAILED);
  if(mode==1||mode==7)assert(f.time==0&&f.tx==1);
  if(mode==2||mode==3)assert(f.time==1&&f.tx==1&&f.requests==0);
  if(mode==4)assert(f.tx==259&&f.requests==0);
  if(mode>=8){assert(f.tx==cut+2&&f.requests==0&&route.completed==cut);assert(f.pops==cut+(mode==8?2u:3u));unsigned prior=f.calls;struct mr_io io={&queue,mq_send_checked,mq_recv_slot};assert(mst_run_once(&route,&io,3)==MT_BUSY&&f.calls==prior);}
  unsigned calls=f.calls;assert(ms_claim(&plan)==-1&&f.calls==calls);
 }
#ifdef MASTER_A53_EMULATION
 master_emulation_full_setup_pass();
#else
 puts("MASTER_FULL_SETUP_COMPOSITION_PASS cases=16 sends=259 pops=260");
#endif
 return 0;
}
