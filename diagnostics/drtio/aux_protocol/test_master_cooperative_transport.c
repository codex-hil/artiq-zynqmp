/* SPDX-License-Identifier: LGPL-3.0-or-later */
/* Fake foreground scheduling only, not lwIP wall-time or stuck-AXI recovery. */
#include <assert.h>
#include <stdio.h>
#include "master_star_step.h"
#include "master_route_queue.h"
#include "master_aux_mmio.h"
struct coop_fake {const uint8_t *ack;unsigned mode,cut,ops,commits,pops,management,in_step,high;uint32_t present,pointer,length;uint8_t tx[40];};
static void op(struct coop_fake *f){assert(f->in_step);f->ops++;}
static int coop_read(void *ctx,uint32_t a,uint32_t *v){
 struct coop_fake *f=ctx;op(f);
 if(a==0xa0000800)*v=0x47534d31;else if(a==0xa0000804)*v=3;else if(a==0xa0000808)*v=125000000;
 else if(a==MM_TX_BUSY)*v=0;else if(a==MM_TX_LENGTH)*v=f->length;
 else if(a==MM_RX_PRESENT)*v=f->present;else if(a==MM_RX_POINTER)*v=f->pointer;
 else if(a==MM_RX_ERROR)*v=f->mode==5?1:0;
 else {assert(f->present);unsigned i=a-(MM_RX_MEMORY+1024*f->pointer);assert(i==0||i==4);
  *v=(uint32_t)f->ack[i]|((uint32_t)f->ack[i+1]<<8)|((uint32_t)f->ack[i+2]<<16)|((uint32_t)f->ack[i+3]<<24);
  if(f->mode==2&&f->commits-1==f->cut&&i==4)*v^=0x1000000;
 }
 return 0;
}
static int coop_write(void *ctx,uint32_t a,uint32_t v){
 struct coop_fake *f=ctx;op(f);
 if(a==MM_TX_LENGTH)f->length=v;
 else if(a==MM_TX_BUSY){
  unsigned stage=f->commits++;assert(stage<257&&!f->present&&v==1);
  assert(f->tx[0]==(stage<256?0x30:0x31)&&f->length==(stage<256?40u:8u));
  if(stage<256){assert(f->tx[1]==stage);for(unsigned i=0;i<32;i++){unsigned expected=0xff;if(stage==0&&i==0)expected=0;if(stage==1&&i==0)expected=1;if(stage==1&&i==1)expected=0;assert(f->tx[2+i]==expected);}}
  if(f->mode!=1||stage!=f->cut)f->present=1;
 }else if(a==MM_RX_PRESENT){assert(f->present&&v==1);f->present=0;f->pops++;f->pointer=(f->pointer+1)%8;}
 else {assert(a>=MM_TX_MEMORY&&a<MM_TX_MEMORY+40);unsigned i=a-MM_TX_MEMORY;for(unsigned j=0;j<4;j++)f->tx[i+j]=(uint8_t)(v>>(8*j));}
 return 0;
}
static int coop_fence(void *ctx){op(ctx);return 0;}
struct coop_io {struct coop_fake *f;struct mq_transport *q;};
static int coop_send(void *ctx,const uint8_t *p,size_t n){struct coop_io *io=ctx;io->f->high++;return mq_send_checked(io->q,p,n);}
static int coop_recv(void *ctx,uint32_t *kind){struct coop_io *io=ctx;io->f->high++;return mq_recv_slot(io->q,kind);}
static unsigned exercise(const uint8_t *ack,unsigned mode,unsigned cut){
 struct coop_fake f={.ack=ack,.mode=mode,.cut=cut,.in_step=1};struct mm_transport m;struct mm_bus bus={&f,coop_read,coop_write,coop_fence};assert(mm_bind(&m,&bus,3,1)==0);f.in_step=0;
 if(mode==4)f.present=1;
 struct mq_transport q={.rx={&m,mm_acquire,mm_release},.ctx=&m,.pending=mm_pending,.send=mm_send};struct coop_io bridge={&f,&q};struct mr_io io={&bridge,coop_send,coop_recv};struct msi_table state;assert(msi_init_epoch(&state,3,1)==0);
 unsigned steps=0,max_ops=0;int result=0;
 while(!result){
  /* Opportunity for unrelated management command before EVERY step. */
  f.management++;unsigned before=f.ops,high=f.high;f.in_step=1;
  result=msi_step(&state,&io);f.in_step=0;steps++;
  assert(f.high-high<=1);unsigned delta=f.ops-before;if(delta>max_ops)max_ops=delta;
  if(mode==3&&f.commits==cut+1&&!state.terminal){msi_cancel(&state);result=msi_step(&state,&io);}
  assert(steps<=1028);
 }
 assert(f.management==steps&&max_ops<=22);
 if(!mode)assert(result==1&&steps==514&&f.commits==257&&f.pops==257&&f.pointer==1);
 else assert(result<0);
 if(mode==1)assert(f.commits==cut+1&&f.pops==cut);
 if(mode==2)assert(f.commits==cut+1&&f.pops==cut+1);
 if(mode==3)assert(f.commits==cut+1&&f.pops==cut&&f.present==1&&state.tx.commit_attempted==1);
 if(mode>=4)assert(f.commits==0&&f.pops==0);
 unsigned before=f.ops,high=f.high;assert(msi_step(&state,&io)==result&&f.ops==before&&f.high==high);
 return max_ops;
}
int master_cooperative_transport_test(const uint8_t *ack,size_t n){
 assert(n==8);unsigned max=exercise(ack,0,0),cases=1;const unsigned cuts[4]={0,127,255,256};
 for(unsigned mode=1;mode<=3;mode++)for(unsigned i=0;i<4;i++){unsigned v=exercise(ack,mode,cuts[i]);if(v>max)max=v;cases++;}
 exercise(ack,4,0);exercise(ack,5,0);cases+=2;
 printf("MASTER_COOPERATIVE_TRANSPORT_PASS cases=%u max_mock_bus_ops_per_step=%u\n",cases,max);return 0;
}
