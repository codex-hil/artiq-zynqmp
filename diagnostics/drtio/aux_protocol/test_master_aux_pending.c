/* SPDX-License-Identifier: LGPL-3.0-or-later */
#include <assert.h>
#include <stdio.h>
#include "master_aux_pending.h"
#include "master_control_codec.h"
struct fake {struct map_request *request;const uint8_t *frames;unsigned calls,commits,pops,mode,empty_polls,fail_at,cancel_at;uint32_t pointer,present,length;uint8_t memory[1024];};
static int tick(struct fake *f){f->calls++;if(f->calls==f->cancel_at)map_cancel(f->request);return f->calls==f->fail_at?-1:0;}
static int read_reg(void *ctx,uint32_t a,uint32_t *v){
 struct fake *f=ctx;if(tick(f))return -1;
 if(a==MM_RX_ERROR)*v=0;
 else if(a==MM_RX_PRESENT){*v=f->present;if(f->request->phase==MAP_RX&&(f->mode==1||(f->mode==2&&f->empty_polls++<2)))*v=0;}
 else if(a==MM_RX_POINTER)*v=f->pointer;
 else if(a==MM_TX_LENGTH)*v=f->length;
 else if(a==MM_TX_BUSY)*v=0;
 else {assert(f->present&&a>=MM_RX_MEMORY+f->pointer*1024&&a<MM_RX_MEMORY+f->pointer*1024+8);unsigned offset=a-(MM_RX_MEMORY+f->pointer*1024);unsigned frame=f->mode==4?0:2;const uint8_t *bytes=f->frames+8*frame;*v=(uint32_t)bytes[offset]|((uint32_t)bytes[offset+1]<<8)|((uint32_t)bytes[offset+2]<<16)|((uint32_t)bytes[offset+3]<<24);if(f->mode==3&&offset==4)*v^=1;}
 return 0;
}
static int write_reg(void *ctx,uint32_t a,uint32_t v){
 struct fake *f=ctx;int error=tick(f); /* Ambiguous failure may already apply. */
 if(a==MM_TX_LENGTH)f->length=v;
 else if(a==MM_TX_BUSY){assert(v==1&&++f->commits==1&&f->request->tx.commit_attempted);f->present=1;}
 else if(a==MM_RX_PRESENT){assert(v==1&&f->present&&++f->pops==1&&f->request->rx.release_attempted);f->present=0;}
 else {assert(a>=MM_TX_MEMORY&&a<MM_TX_MEMORY+1024);unsigned offset=a-MM_TX_MEMORY;for(unsigned j=0;j<4;j++){f->memory[offset+j]=(uint8_t)(v>>(8*j));}}
 return error;
}
static int fence(void *ctx){return tick(ctx);}
int master_aux_pending_test(const uint8_t *frames,size_t size){
 assert(size==40);unsigned cases=0;
 for(unsigned packet=0;packet<2;packet++)for(unsigned mode=0;mode<5;mode++){
  /* Actual Rust canonical path40B or rank8B, fixed RoutingAck via strict Rust. */
  uint8_t encoded[40];int length=packet?aux_master_leaf_encode(0x31,1,encoded,sizeof(encoded)):aux_master_star_path_encode(1,encoded,sizeof(encoded));assert(length==(packet?8:40));
  unsigned normal=(unsigned)length/4+22; /* TX(words+10) +RX12bus, plus1decode-onlyturn. */
  unsigned variants=mode==0?1+2*normal:1;
  for(unsigned variant=0;variant<variants;variant++){
   struct map_request request={0};struct fake f={.request=&request,.frames=frames,.pointer=cases%8,.mode=mode};
   if(variant&&variant<=normal){f.fail_at=variant;}
   if(variant>normal){f.cancel_at=variant-normal;}
   struct mm_transport mm={.bus={&f,read_reg,write_reg,fence},.budget=3,.bound=1};
   ma_fixed_decoder decoder=mode==4?aux_master_control_decode:aux_master_routing_ack_decode;
   assert(!map_begin(&request,&mm,encoded,(size_t)length,decoder,0x32,1));assert(map_begin(&request,&mm,encoded,(size_t)length,decoder,0x32,1)==MAP_INVALID);
   int result=0;unsigned turns=0;
   while(!result){unsigned before=f.calls;result=map_step(&request);assert(f.calls-before<=1&&++turns<normal+12);if(f.cancel_at&&f.calls==f.cancel_at)assert(result==MAP_CANCELLED);if(result!=1)assert(!request.kind);}
   if(!variant&&(mode==0||mode==2)){assert(result==1&&request.kind==0x32&&f.commits==1&&f.pops==1&&turns==normal+1+(mode==2?4u:0u));}
   else {assert(result<0&&!request.kind&&mm.failed);}
   if(mode==3){assert(result==MAR_PACKET&&f.pops==1);}
   if(mode==4){assert(result==MAP_UNEXPECTED&&f.pops==1);}
   if(f.commits){for(int i=0;i<length;i++){assert(f.memory[i]==encoded[i]);}}
   unsigned calls=f.calls,commits=f.commits,pops=f.pops;assert(map_step(&request)==result&&f.calls==calls&&f.commits==commits&&f.pops==pops);map_cancel(&request);assert(map_step(&request)==result&&f.calls==calls);
   cases++;
  }
 }
 printf("MASTER_AUX_PENDING_PASS cases=%u max_callbacks_per_turn=1\n",cases);return 0;
}
