/* SPDX-License-Identifier: LGPL-3.0-or-later */
#pragma once
/* Shared test-only fake bus/peer and action callbacks. Caller supplies assert. */
#include "master_control_codec.h"
#include "master_rt_setup.h"
#include "master_route_queue.h"
#include "master_star_setup.h"
#include "master_setup_sequence.h"
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
