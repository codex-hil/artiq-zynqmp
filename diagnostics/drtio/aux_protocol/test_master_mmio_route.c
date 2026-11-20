/* SPDX-License-Identifier: LGPL-3.0-or-later */
#ifdef MASTER_A53_EMULATION
extern void master_emulation_assert(int);
extern void master_emulation_route_pass(void);
#define assert(condition) master_emulation_assert(!!(condition))
#else
#include <assert.h>
#include <stdio.h>
#endif
#include "master_aux_mmio.h"
#include "master_route_queue.h"
struct full_mock {uint8_t ack[8],tx[1024];unsigned calls,fail_at,commits,pops,mode;
 uint32_t length,present,pointer;};
static int full_fault(struct full_mock *m){return ++m->calls==m->fail_at;}
static int full_read(void *ctx,uint32_t a,uint32_t *v){
 struct full_mock *m=ctx;if(full_fault(m))return -1;
 if(a==0xa0000800)*v=0x47534d31;
 else if(a==0xa0000804)*v=3;
 else if(a==0xa0000808)*v=125000000;
 else if(a==MM_RX_ERROR)*v=m->mode==2?1:0;
 else if(a==MM_RX_PRESENT)*v=m->present;
 else if(a==MM_RX_POINTER)*v=m->pointer;
 else if(a==MM_TX_LENGTH)*v=m->length;
 else if(a==MM_TX_BUSY)*v=0;
 else {
  assert(a==MM_RX_MEMORY+m->pointer*1024||a==MM_RX_MEMORY+m->pointer*1024+4);
  unsigned k=(a-MM_RX_MEMORY)%1024;
  *v=(uint32_t)m->ack[k]|((uint32_t)m->ack[k+1]<<8)|((uint32_t)m->ack[k+2]<<16)|((uint32_t)m->ack[k+3]<<24);
  if(m->mode==3&&k==4)*v^=0x1000000;
 }
 return 0;
}
static int full_write(void *ctx,uint32_t a,uint32_t v){
 struct full_mock *m=ctx;
 if(a==MM_TX_BUSY){
  assert(v==1&&m->commits<2&&!m->present);
  unsigned stage=m->commits++;
  assert(m->length==(stage?8u:40u)&&m->tx[0]==0x30+stage&&m->tx[1]==1);
  if(!stage){assert(m->tx[2]==1);for(unsigned i=3;i<34;i++)assert(!m->tx[i]);}
  if(m->mode!=4)m->present=1;
 } else if(a==MM_RX_PRESENT){assert(v==1&&m->present);m->pops++;m->present=0;m->pointer=(m->pointer+1)%8;}
 else if(a==MM_TX_LENGTH)m->length=v;
 else {
  assert(a>=MM_TX_MEMORY&&a<MM_TX_MEMORY+1024&&a%4==0);
  unsigned i=a-MM_TX_MEMORY;
  for(unsigned j=0;j<4;j++)m->tx[i+j]=(uint8_t)(v>>(j*8));
 }
 return full_fault(m)?-1:0;
}
static int full_fence(void *ctx){return full_fault(ctx)?-1:0;}
static unsigned full_run(const uint8_t *ack,unsigned fault,unsigned mode){
 struct full_mock f={.fail_at=fault,.mode=mode};for(unsigned i=0;i<8;i++)f.ack[i]=ack[i];
 if(mode==1)f.present=1;
 struct mm_transport transport;struct mm_bus bus={&f,full_read,full_write,full_fence};
 struct mr_setup setup;mr_init_epoch(&setup);
 int result=mm_bind(&transport,&bus,3,1);
 if(result==0){
  struct mq_transport q={.rx={&transport,mm_acquire,mm_release},.ctx=&transport,.pending=mm_pending,.send=mm_send};
  result=mq_route_once(&setup,&q,3);
  unsigned calls=f.calls;
  assert(mq_route_once(&setup,&q,3)==MT_BUSY&&f.calls==calls);
 }
 if(!fault&&!mode){assert(result==0&&f.commits==2&&f.pops==2&&setup.completed==2);}
 else {assert(result<0&&f.commits<=2&&f.pops<=2);}
 if(mode==1||mode==2)assert(f.commits==0&&f.pops==0);
 if(mode==3)assert(f.commits==1&&f.pops==1&&setup.completed==0);
 if(mode==4)assert(f.commits==1&&f.pops==0&&setup.completed==0);
 return f.calls;
}
int master_mmio_route_test(const uint8_t *ack,size_t n){
 assert(n==8);unsigned calls=full_run(ack,0,0);
#ifdef FORCE_ROUTE_ASSERT
 assert(calls==64); /* Deliberately false negative control, never normal build. */
#endif
 assert(calls==63);
 for(unsigned fault=1;fault<=calls;fault++)full_run(ack,fault,0);
 for(unsigned mode=1;mode<=4;mode++)full_run(ack,0,mode);
#ifdef MASTER_A53_EMULATION
 master_emulation_route_pass();
#else
 printf("MASTER_FULL_MMIO_ROUTE_PASS baseline_callbacks=%u failure_points=%u controls=4\n",calls,calls);
#endif
 return 0;
}
