/* SPDX-License-Identifier: LGPL-3.0-or-later */
#pragma once
#include <stdint.h>
#include <stddef.h>
/* Isolated callback-only candidate, NOT direct volatile MMIO or firmware.
 * Caller confirms exact reviewed map, sole link/CPU ownership and live target
 * clock/reset epoch. Identity reads below do NOT prove map hash or ownership.
 * Each callback must itself finish; poll limits cannot bound a hung AXI access.
 * Failure poisons transport; never retry commits/releases or clear RX errors.
 */
#define MM_TX_LENGTH UINT32_C(0xa0002000)
#define MM_TX_BUSY UINT32_C(0xa0002004)
#define MM_RX_PRESENT UINT32_C(0xa0002008)
#define MM_RX_ERROR UINT32_C(0xa000200c)
#define MM_RX_POINTER UINT32_C(0xa0002010)
#define MM_TX_MEMORY UINT32_C(0xa0010000)
#define MM_RX_MEMORY UINT32_C(0xa0012000)
struct mm_bus {void *ctx;int (*read)(void *,uint32_t,uint32_t *);
 int (*write)(void *,uint32_t,uint32_t);int (*fence)(void *);};
struct mm_transport {struct mm_bus bus;uint32_t budget;unsigned bound,failed,held,commit_attempted,release_attempted;
 uint32_t pointer;uint8_t snapshot[1024];};
static inline int mm_fail(struct mm_transport *m){m->failed=1;return -1;}
static inline int mm_read(struct mm_transport *m,uint32_t a,uint32_t *v){
 if(m->bus.read(m->bus.ctx,a,v))return mm_fail(m);
 return 0;
}
static inline int mm_bind(struct mm_transport *m,const struct mm_bus *b,uint32_t budget,int reviewed_map_owner_epoch) {
 if(!m||!b||!b->read||!b->write||!b->fence||!budget||budget>1024||reviewed_map_owner_epoch!=1)return -1;
 *m=(struct mm_transport){.bus=*b,.budget=budget};
 const uint32_t a[3]={0xa0000800,0xa0000804,0xa0000808},expected[3]={0x47534d31,3,125000000};
 for(unsigned i=0;i<3;i++){uint32_t v;if(mm_read(m,a[i],&v)||v!=expected[i])return mm_fail(m);}
 m->bound=1;return 0;
}
static inline int mm_ready(struct mm_transport *m){return m&&m->bound&&!m->failed;}
static inline int mm_pending(void *ctx){
 struct mm_transport *m=ctx;uint32_t error,present;
 if(!mm_ready(m))return -1;
 if(mm_read(m,MM_RX_ERROR,&error)||error||mm_read(m,MM_RX_PRESENT,&present)||present>1)return mm_fail(m);
 return (int)present;
}
static inline int mm_wait_tx(struct mm_transport *m){
 for(uint32_t i=0;i<m->budget;i++){uint32_t busy;
  if(mm_read(m,MM_TX_BUSY,&busy)||busy>1)return mm_fail(m);
  if(!busy)return 0;
 }
 return mm_fail(m);
}
static inline int mm_send(void *ctx,const uint8_t *bytes,size_t n){
 struct mm_transport *m=ctx;
 if(!mm_ready(m)||!bytes||n<4||n>1024||n%4||m->held)return -1;
 if(mm_pending(m)!=0)return mm_fail(m);
 if(mm_wait_tx(m))return -1;
 for(size_t i=0;i<n;i+=4){uint32_t v=(uint32_t)bytes[i]|((uint32_t)bytes[i+1]<<8)|((uint32_t)bytes[i+2]<<16)|((uint32_t)bytes[i+3]<<24);
  if(m->bus.write(m->bus.ctx,MM_TX_MEMORY+(uint32_t)i,v))return mm_fail(m);
 }
 if(m->bus.fence(m->bus.ctx)||m->bus.write(m->bus.ctx,MM_TX_LENGTH,(uint32_t)n))return mm_fail(m);
 uint32_t length;
 if(mm_read(m,MM_TX_LENGTH,&length)||length!=n||m->bus.fence(m->bus.ctx))return mm_fail(m);
 m->commit_attempted=1;
 if(m->bus.write(m->bus.ctx,MM_TX_BUSY,1)||m->bus.fence(m->bus.ctx))return mm_fail(m);
 return mm_wait_tx(m);
}
/* Fixed RoutingAck prefix snapshot only, rest initialized0 storage. Not a
 * generic1024-byte packet copy or received-length qualification. */
static inline int mm_acquire(void *ctx,const uint8_t **slot,size_t *size,uint32_t *ticket){
 struct mm_transport *m=ctx;uint32_t pointer,v,error,after;
 if(!mm_ready(m)||!slot||!size||!ticket||m->held)return -1;
 int present=mm_pending(m);if(present<=0)return present;
 if(mm_read(m,MM_RX_POINTER,&pointer)||pointer>7)return mm_fail(m);
 for(unsigned i=0;i<8;i+=4){
  if(mm_read(m,MM_RX_MEMORY+pointer*1024+i,&v))return -1;
  for(unsigned j=0;j<4;j++)m->snapshot[i+j]=(uint8_t)(v>>(j*8));
 }
 if(mm_read(m,MM_RX_ERROR,&error)||error||mm_read(m,MM_RX_POINTER,&after)||after!=pointer)return mm_fail(m);
 m->held=1;m->pointer=pointer;*ticket=pointer;*slot=m->snapshot;*size=1024;return 1;
}
static inline int mm_release(void *ctx,uint32_t ticket){
 struct mm_transport *m=ctx;uint32_t pointer,present,error;
 if(!mm_ready(m)||!m->held||ticket!=m->pointer)return -1;
 if(mm_read(m,MM_RX_ERROR,&error)||error||mm_read(m,MM_RX_POINTER,&pointer)||pointer!=ticket||mm_read(m,MM_RX_PRESENT,&present)||present!=1)return mm_fail(m);
 m->held=0;m->release_attempted=1;
 if(m->bus.write(m->bus.ctx,MM_RX_PRESENT,1)||m->bus.fence(m->bus.ctx))return mm_fail(m);
 return 0;
}
