/* SPDX-License-Identifier: LGPL-3.0-or-later */
#include <assert.h>
#include <stdio.h>
#include "master_aux_resumable_rx.h"
struct fake {struct mar_session *s;unsigned calls,fail_at,cancel_at,pops,mode,empty_polls,decode_calls;uint32_t pointer;uint8_t bytes[8];};
static struct fake *decoder_context;
static int tick(struct fake *f){f->calls++;if(f->calls==f->cancel_at)mar_cancel(f->s);return f->calls==f->fail_at?-1:0;}
static int read_reg(void *ctx,uint32_t a,uint32_t *v){
 struct fake *f=ctx;assert(!f->s->kind);if(tick(f))return -1;
 if(a==MM_RX_ERROR)*v=f->mode==1?1:0;
 else if(a==MM_RX_PRESENT)*v=f->mode==2||(f->mode==3&&f->empty_polls++<2)?0:f->mode==4?2:f->mode==8&&f->s->phase==10?0:1;
 else if(a==MM_RX_POINTER)*v=f->mode==5?8:(f->mode==6&&f->s->phase==6)||(f->mode==7&&f->s->phase==9)?(f->pointer+1)%8:f->pointer;
 else {assert(a==MM_RX_MEMORY+f->pointer*1024||a==MM_RX_MEMORY+f->pointer*1024+4);unsigned i=a-(MM_RX_MEMORY+f->pointer*1024);*v=(uint32_t)f->bytes[i]|((uint32_t)f->bytes[i+1]<<8)|((uint32_t)f->bytes[i+2]<<16)|((uint32_t)f->bytes[i+3]<<24);}
 return 0;
}
static int write_reg(void *ctx,uint32_t a,uint32_t v){
 struct fake *f=ctx;assert(a==MM_RX_PRESENT&&v==1&&f->s->release_attempted&&f->s->mm->release_attempted&&!f->s->mm->held&&!f->s->kind);
 int error=tick(f);assert(++f->pops==1);return error; /* Possibly applied even on failure. */
}
static int fence(void *ctx){struct fake *f=ctx;assert(!f->s->kind);return tick(f);}
/* Standalone ownership test decoder, not CRC/protocol acceptance proof. */
static int32_t decode(const uint8_t *bytes,size_t size){
 struct fake *f=decoder_context;assert(size==8&&f->s->mm->held&&!f->s->kind);f->decode_calls++;
 for(unsigned i=0;i<8;i++)assert(bytes[i]==f->bytes[i]);
 if(f->mode==10)mar_cancel(f->s);
 return f->mode==9?-1:0x32;
}
int main(void){
 unsigned cases=0;
 for(unsigned pointer=0;pointer<8;pointer++)for(unsigned mode=0;mode<=10;mode++){
  unsigned variants=mode==0?25:1; /* baseline +12callback errors +12cancels */
  for(unsigned variant=0;variant<variants;variant++){
   struct mar_session s={0};struct fake f={.s=&s,.mode=mode,.pointer=pointer};decoder_context=&f;
   for(unsigned i=0;i<8;i++){f.bytes[i]=(uint8_t)(pointer*16+i);}
   if(variant&&variant<=12){f.fail_at=variant;}
   if(variant>12){f.cancel_at=variant-12;}
   struct mm_transport mm={.bus={&f,read_reg,write_reg,fence},.budget=3,.bound=1};
   assert(!mar_begin(&s,&mm,decode,1));assert(mar_begin(&s,&mm,decode,1)==MAR_INVALID);
   int result=0;unsigned turns=0;
   while(!result){unsigned before=f.calls;result=mar_step(&s);assert(f.calls-before<=1&&++turns<24);if(f.cancel_at&&f.calls==f.cancel_at)assert(result==MAR_CANCELLED);if(result!=1)assert(!s.kind);}
   if(!variant&&(mode==0||mode==3)){assert(result==1&&s.kind==0x32&&f.pops==1&&!mm.held&&turns==(mode==0?13u:17u));}
   else {assert(result<0&&!s.kind&&mm.failed);}
   if(mode==9){assert(result==MAR_PACKET&&f.pops==1&&f.decode_calls==1&&!mm.held);}
   if(mode==10){assert(result==MAR_CANCELLED&&f.pops==0&&mm.held);}
   if(variant==11||variant==12){assert(s.release_attempted&&f.pops==1&&!mm.held);}
   unsigned calls=f.calls,pops=f.pops,decodes=f.decode_calls;assert(mar_step(&s)==result&&f.calls==calls&&f.pops==pops&&f.decode_calls==decodes);mar_cancel(&s);assert(mar_step(&s)==result&&f.calls==calls);
   cases++;
  }
 }
 /* Loss of software lease between turns must fail before another bus access. */
 for(unsigned pointer=0;pointer<8;pointer++)for(unsigned loss=0;loss<4;loss++){
  struct mar_session s={0};struct fake f={.s=&s,.pointer=pointer};decoder_context=&f;
  struct mm_transport mm={.bus={&f,read_reg,write_reg,fence},.budget=3,.bound=1};assert(!mar_begin(&s,&mm,decode,1));
  unsigned target=loss==0?0:loss==3?12:3;
  while(s.phase<target){assert(mar_step(&s)==0);}
  if(loss==0||loss==3){mm.held=1;}else if(loss==1){mm.held=0;}else{mm.pointer=(pointer+1)%8;}
  unsigned calls=f.calls,pops=f.pops;assert(mar_step(&s)==MAR_IO&&f.calls==calls&&f.pops==pops&&!s.kind&&mm.failed);cases++;
 }
 printf("MASTER_AUX_RESUMABLE_RX_PASS cases=%u max_callbacks_per_turn=1\n",cases);return 0;
}
