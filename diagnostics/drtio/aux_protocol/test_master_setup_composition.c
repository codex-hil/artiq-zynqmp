/* SPDX-License-Identifier: LGPL-3.0-or-later */
/* Test-only fixed-leaf setup composition; not production master service. */
#include <assert.h>
#include <stdio.h>
#include "master_control_codec.h"
#include "master_setup_sequence.h"
#include "master_rt_setup.h"
#include "master_route_queue.h"
struct setup_fake {const uint8_t *frames;unsigned mode,calls,tx,time,requests,pops;uint32_t present,pointer,length,force,count;uint8_t txbytes[40];const uint8_t *reply;};
static void enqueue(struct setup_fake *f,unsigned frame){assert(!f->present);f->reply=f->frames+frame*8;f->present=1;}
static int setup_read(void *ctx,uint32_t a,uint32_t *v){
 struct setup_fake *f=ctx;f->calls++;
 if(a==0xa0000800)*v=0x47534d31;else if(a==0xa0000804)*v=3;else if(a==0xa0000808)*v=125000000;
 else if(a==MRT_RX_UP)*v=f->mode==6?0:1;
 else if(a==MRT_ERROR)*v=f->mode==5&&f->requests?4:0;
 else if(a==MRT_SET_TIME||a==MRT_WAIT||a==MM_TX_BUSY||a==MM_RX_ERROR)*v=0;
 else if(a==MRT_FORCE)*v=f->force;else if(a==MRT_COUNT)*v=f->count;else if(a==MRT_SPACE)*v=16;
 else if(a==MM_RX_PRESENT)*v=f->present;else if(a==MM_RX_POINTER)*v=f->pointer;else if(a==MM_TX_LENGTH)*v=f->length;
 else {assert(f->present&&f->reply);unsigned k=a-(MM_RX_MEMORY+f->pointer*1024);assert(k==0||k==4);*v=(uint32_t)f->reply[k]|((uint32_t)f->reply[k+1]<<8)|((uint32_t)f->reply[k+2]<<16)|((uint32_t)f->reply[k+3]<<24);}
 return 0;
}
static int setup_write(void *ctx,uint32_t a,uint32_t v){
 struct setup_fake *f=ctx;f->calls++;
 if(a==MM_TX_LENGTH)f->length=v;
 else if(a==MM_TX_BUSY){
  const unsigned kinds[4]={0,0x30,0x31,0x20};assert(f->tx<4&&f->txbytes[0]==kinds[f->tx]);
  assert(f->length==(f->tx==1?40u:8u));
  if(f->tx==0)enqueue(f,f->mode==7?1:0);else if(f->tx<3)enqueue(f,2);else enqueue(f,f->mode==4?4:3);
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
int master_setup_composition_test(const uint8_t *frames,size_t length){
 assert(length==40);
 for(unsigned mode=0;mode<8;mode++){
  struct setup_fake f={.frames=frames,.mode=mode};struct mm_bus bus={&f,setup_read,setup_write,setup_fence};struct mm_transport m;
  assert(mm_bind(&m,&bus,3,1)==0);struct mrt_setup rt={.mm=&m};struct ma_slot_state slot={0};
  struct mq_transport queue={.rx={&m,mm_acquire,mm_release},.ctx=&m,.pending=mm_pending,.send=mm_send};struct mr_setup route;mr_init_epoch(&route);
  struct ms_setup plan;assert(ms_init_epoch(&plan,3,1)==0);
  for(unsigned action=MS_LINK;action<=MS_BUFFER;action++){
   assert(ms_claim(&plan)==(int)action);int result=-1;
   switch(action){
    case MS_LINK:result=mrt_live(&m);break;
    case MS_ECHO:result=control_exchange(&m,&slot,0,0,1);break;
    case MS_SET_TIME:result=mm_pending(&m)==0?mrt_set_time_once(&rt):-1;break;
    case MS_TSC_ACK:result=control_reply(&m,&slot,4);break;
    case MS_ROUTING:result=mq_route_once(&route,&queue,3);break;
    case MS_STATUS:result=control_exchange(&m,&slot,0x20,1,0x22);break;
    case MS_BUFFER:result=mrt_buffer_once(&rt);break;
    default:assert(0);
   }
   if(result){assert(ms_result(&plan,-9)==-9);break;}assert(ms_result(&plan,1)==0);
  }
  if(!mode){assert(plan.action==MS_COMPLETE&&f.tx==4&&f.time==1&&f.requests==1&&f.pops==5&&rt.credits==16);}
  else assert(plan.action==MS_FAILED);
  if(mode==1||mode==7)assert(f.time==0&&f.tx==1);
  if(mode==2||mode==3)assert(f.time==1&&f.tx==1&&f.requests==0);
  if(mode==4)assert(f.tx==4&&f.requests==0);
  unsigned calls=f.calls;assert(ms_claim(&plan)==-1&&f.calls==calls);
 }
 puts("MASTER_SETUP_COMPOSITION_PASS cases=8");return 0;
}
