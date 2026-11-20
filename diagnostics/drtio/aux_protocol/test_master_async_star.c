/* SPDX-License-Identifier: LGPL-3.0-or-later */
#include <assert.h>
#include <stdio.h>
#include "master_async_star.h"
struct fake {struct mas_table *table;const uint8_t *ack;unsigned calls,commits,pops,cut,mode,empty_polls;uint32_t pointer,present,length;uint8_t memory[40];};
static int read_reg(void *ctx,uint32_t a,uint32_t *v){
 struct fake *f=ctx;f->calls++;
 if(a==MM_RX_ERROR||a==MM_TX_BUSY)*v=0;
 else if(a==MM_RX_PRESENT){*v=f->present;if(f->mode==7&&f->commits==f->cut+1&&f->table->request.phase==MAP_RX&&f->empty_polls++<2)*v=0;}
 else if(a==MM_RX_POINTER)*v=f->pointer;
 else if(a==MM_TX_LENGTH)*v=f->length;
 else {assert(f->present);unsigned offset=a-(MM_RX_MEMORY+f->pointer*1024);assert(offset==0||offset==4);*v=(uint32_t)f->ack[offset]|((uint32_t)f->ack[offset+1]<<8)|((uint32_t)f->ack[offset+2]<<16)|((uint32_t)f->ack[offset+3]<<24);if(f->mode==2&&f->commits==f->cut+1&&offset==4)*v^=1;}
 return 0;
}
static int write_reg(void *ctx,uint32_t a,uint32_t v){
 struct fake *f=ctx;f->calls++;
 if(a==MM_TX_LENGTH)f->length=v;
 else if(a==MM_TX_BUSY){
  unsigned stage=f->commits;assert(stage<257&&v==1&&f->table->completed==stage&&!f->present);
  assert(f->table->request.tx.commit_attempted);
  if(stage<256){assert(f->length==40&&f->memory[0]==0x30&&f->memory[1]==stage);
   for(unsigned i=0;i<32;i++){unsigned hop=0xff;if(stage==0&&i==0)hop=0;if(stage==1&&i==0)hop=1;if(stage==1&&i==1)hop=0;assert(f->memory[i+2]==hop);}
  }else {assert(f->length==8&&f->memory[0]==0x31&&f->memory[1]==1);}
  f->commits++;if(!(f->mode==1&&stage==f->cut))f->present=1;
  if(stage==f->cut&&f->mode==3)return -1; /* Applied commit, unknown result. */
  if(stage==f->cut&&f->mode==4)mas_cancel(f->table);
 }else if(a==MM_RX_PRESENT){assert(v==1&&f->present&&f->table->request.rx.release_attempted);f->present=0;f->pops++;f->pointer=(f->pointer+1)%8;}
 else {assert(a>=MM_TX_MEMORY&&a<MM_TX_MEMORY+40);unsigned offset=a-MM_TX_MEMORY;for(unsigned j=0;j<4;j++){f->memory[offset+j]=(uint8_t)(v>>(8*j));}}
 return 0;
}
static int fence(void *ctx){((struct fake *)ctx)->calls++;return 0;}
int master_async_star_test(const uint8_t *ack,size_t size){
 assert(size==8&&aux_master_routing_ack_decode(ack,size)==0x32);unsigned cases=0;
 for(unsigned mode=0;mode<=7;mode++){
  unsigned variants=mode>=1&&mode<=4?257:mode==7?2:1;
  for(unsigned cut=0;cut<variants;cut++){
   struct mas_table table={0};struct fake f={.table=&table,.ack=ack,.mode=mode,.cut=mode==7&&cut?256:cut};
   struct mm_transport mm={.bus={&f,read_reg,write_reg,fence},.bound=1,.budget=3};
   uint32_t budget=mode==5?8729:mode==6?1:mode==7?8734:8730;
   assert(!mas_begin(&table,&mm,budget,1)&&mas_begin(&table,&mm,budget,1)==MAS_INVALID);
   int result=0;unsigned turns=0,management=0;
   while(!result){management++;unsigned before=f.calls;result=mas_step(&table);assert(f.calls-before<=1&&++turns<=budget);}
   assert(turns==management);
   if(mode==0||mode==7){assert(result==1&&table.completed==257&&table.requests_started==257&&f.commits==257&&f.pops==257&&turns==budget);}
   else {assert(result<0&&mm.failed);}
   if(mode>=1&&mode<=4){assert(table.completed==f.cut&&table.requests_started==f.cut+1&&f.commits==f.cut+1);assert(f.pops==f.cut+(mode==2));}
   if(mode==3||mode==4){assert(f.present&&table.request.tx.commit_attempted);}
   if(mode==4){assert(result==MAS_CANCELLED);}
   if(mode==5){assert(result==MAS_BUDGET&&table.completed==256&&f.commits==257&&f.pops==257&&!table.request.kind);}
   if(mode==6){assert(result==MAS_BUDGET&&!f.calls&&!f.commits);}
   unsigned calls=f.calls,commits=f.commits,pops=f.pops;assert(mas_step(&table)==result&&f.calls==calls&&f.commits==commits&&f.pops==pops);mas_cancel(&table);assert(mas_step(&table)==result&&f.calls==calls);
   cases++;
  }
 }
 printf("MASTER_ASYNC_STAR_PASS cases=%u healthy_turns=8730 max_callbacks_per_turn=1\n",cases);return 0;
}
