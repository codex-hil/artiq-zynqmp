/* SPDX-License-Identifier: LGPL-3.0-or-later */
#include <assert.h>
#include <stdio.h>
#include "master_aux_mmio.h"
struct fake {unsigned calls,fail_at,commits,pops,profile_bad;uint32_t pointer,present,error,length,busy;};
static int fail(struct fake *f){return ++f->calls==f->fail_at;}
static int rd(void *ctx,uint32_t a,uint32_t *v){
 struct fake *f=ctx;if(fail(f))return -1;
 if(a==0xa0000800)*v=f->profile_bad?0:0x47534d31;
 else if(a==0xa0000804)*v=3;
 else if(a==0xa0000808)*v=125000000;
 else if(a==MM_RX_ERROR)*v=f->error;
 else if(a==MM_RX_PRESENT)*v=f->present;
 else if(a==MM_RX_POINTER)*v=f->pointer;
 else if(a==MM_TX_LENGTH)*v=f->length;
 else if(a==MM_TX_BUSY)*v=f->busy;
 else {assert(a>=MM_RX_MEMORY&&a<MM_RX_MEMORY+8192&&a%4==0);*v=0x11223344;}
 return 0;
}
static int wr(void *ctx,uint32_t a,uint32_t v){
 struct fake *f=ctx;
 /* Simulate uncertain side effect even on failed committing write. */
 if(a==MM_TX_BUSY){assert(v==1);f->commits++;}
 else if(a==MM_RX_PRESENT){assert(v==1);f->pops++;f->pointer=(f->pointer+1)%8;f->present=0;}
 else if(a==MM_TX_LENGTH)f->length=v;
 else assert(a>=MM_TX_MEMORY&&a<MM_TX_MEMORY+1024&&a%4==0);
 return fail(f)?-1:0;
}
static int fence(void *ctx){return fail(ctx)?-1:0;}
static void init(struct mm_transport *m,struct fake *f){struct mm_bus b={f,rd,wr,fence};assert(mm_bind(m,&b,3,1)==0);}
int main(void){
 uint8_t bytes[8]={0x30,1,1};unsigned scenarios=0,txcalls,rxcalls;
 struct fake f={0};struct mm_transport m;init(&m,&f);assert(mm_send(&m,bytes,8)==0);txcalls=f.calls;
 assert(f.commits==1&&m.commit_attempted);scenarios++;
 for(unsigned fault=1;fault<=txcalls;fault++){
  struct fake x={.fail_at=fault};struct mm_transport t;struct mm_bus b={&x,rd,wr,fence};
  int result=mm_bind(&t,&b,3,1);if(!result)result=mm_send(&t,bytes,8);
  assert(result==-1&&t.failed&&x.commits<=1);
  unsigned calls=x.calls;assert(mm_send(&t,bytes,8)==-1&&x.calls==calls);scenarios++;
 }
 f=(struct fake){.present=1,.pointer=7};init(&m,&f);const uint8_t *slot=0;size_t size=0;uint32_t ticket=99;
 assert(mm_acquire(&m,&slot,&size,&ticket)==1&&ticket==7&&size==1024&&slot[0]==0x44&&slot[3]==0x11);
 assert(mm_release(&m,ticket)==0&&f.pops==1&&f.pointer==0);rxcalls=f.calls;scenarios++;
 for(unsigned fault=1;fault<=rxcalls;fault++){
  struct fake x={.fail_at=fault,.present=1,.pointer=7};struct mm_transport t;struct mm_bus b={&x,rd,wr,fence};
  int result=mm_bind(&t,&b,3,1);if(!result){result=mm_acquire(&t,&slot,&size,&ticket);if(result==1)result=mm_release(&t,ticket);}
  assert(result==-1&&t.failed&&x.pops<=1);
  unsigned calls=x.calls;assert(mm_pending(&t)==-1&&x.calls==calls);scenarios++;
 }
 for(unsigned mode=0;mode<4;mode++){
  f=(struct fake){0};init(&m,&f);
  if(mode==0){f.busy=1;assert(mm_send(&m,bytes,8)==-1&&f.commits==0);}
  if(mode==1){f.present=1;assert(mm_send(&m,bytes,8)==-1&&f.commits==0&&f.pops==0);}
  if(mode==2){f.error=1;assert(mm_pending(&m)==-1&&f.pops==0);}
  if(mode==3){f.present=1;f.pointer=8;assert(mm_acquire(&m,&slot,&size,&ticket)==-1&&f.pops==0);}
  assert(m.failed);scenarios++;
 }
 f=(struct fake){0};init(&m,&f);unsigned calls=f.calls;
 assert(mm_send(&m,bytes,3)==-1&&mm_send(&m,bytes,1028)==-1&&f.calls==calls);
 f=(struct fake){.profile_bad=1};struct mm_bus b={&f,rd,wr,fence};
 assert(mm_bind(&m,&b,3,1)==-1&&m.failed&&f.commits==0);scenarios++;
 f=(struct fake){0};b.ctx=&f;calls=f.calls;
 assert(mm_bind(&m,&b,3,0)==-1&&f.calls==calls);scenarios++;
 for(unsigned mode=0;mode<3;mode++){
  f=(struct fake){.present=1,.pointer=2};init(&m,&f);
  assert(mm_acquire(&m,&slot,&size,&ticket)==1);
  if(mode==0)f.pointer=3;
  if(mode==1)f.error=1;
  if(mode==2)f.present=0;
  assert(mm_release(&m,ticket)==-1&&m.failed&&f.pops==0);scenarios++;
 }
 uint8_t maximum[1024]={0};f=(struct fake){0};init(&m,&f);
 assert(mm_send(&m,maximum,sizeof(maximum))==0&&f.length==1024&&f.commits==1);scenarios++;
 printf("MASTER_AUX_MOCK_MMIO_PASS scenarios=%u tx_callbacks=%u rx_callbacks=%u\n",scenarios,txcalls,rxcalls);
 return 0;
}
