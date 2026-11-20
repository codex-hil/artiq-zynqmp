/* SPDX-License-Identifier: LGPL-3.0-or-later */
#include <assert.h>
#include <stdio.h>
#include "master_aux_resumable_tx.h"
struct fake {struct mat_session *s;unsigned calls,fail_at,cancel_at,mode,commits,pre_polls,post_polls;uint32_t length;uint8_t memory[1024];};
static int tick(struct fake *f){f->calls++;if(f->calls==f->cancel_at)mat_cancel(f->s);return f->calls==f->fail_at?-1:0;}
static int read_reg(void *ctx,uint32_t a,uint32_t *v){
 struct fake *f=ctx;if(tick(f))return -1;
 if(a==MM_RX_ERROR)*v=f->mode==1?1:0;
 else if(a==MM_RX_PRESENT)*v=f->mode==2?1:0;
 else if(a==MM_TX_LENGTH)*v=f->length+(f->mode==6);
 else {assert(a==MM_TX_BUSY);if(f->mode==5)*v=2;
  else if(f->s->phase==2)*v=f->mode==3||(f->mode==7&&f->pre_polls++<2);
  else *v=f->mode==4||(f->mode==7&&f->post_polls++<2);
 }
 return 0;
}
static int write_reg(void *ctx,uint32_t a,uint32_t v){
 struct fake *f=ctx;if(a==MM_TX_BUSY)assert(f->s->commit_attempted&&f->s->mm->commit_attempted);
 int error=tick(f); /* Writes may apply before an error/cancellation is visible. */
 if(a==MM_TX_LENGTH)f->length=v;
 else if(a==MM_TX_BUSY){assert(v==1&&++f->commits==1);}
 else {assert(a>=MM_TX_MEMORY&&a<MM_TX_MEMORY+1024);unsigned i=a-MM_TX_MEMORY;for(unsigned j=0;j<4;j++)f->memory[i+j]=(uint8_t)(v>>(j*8));}
 return error;
}
static int fence(void *ctx){return tick(ctx);}
int main(void){
 unsigned cases=0;const size_t lengths[3]={8,40,1024};
 for(unsigned k=0;k<3;k++)for(unsigned mode=0;mode<8;mode++){
  size_t length=lengths[k];unsigned normal=(unsigned)(length/4)+10;
  unsigned variants=mode==0?1+2*normal:1;
  for(unsigned variant=0;variant<variants;variant++){
   struct mat_session s={0};struct fake f={.s=&s,.mode=mode};uint8_t input[1024],original[1024];
   for(size_t i=0;i<length;i++)input[i]=original[i]=(uint8_t)(i*17+9);
   if(variant&&variant<=normal)f.fail_at=variant;
   if(variant>normal)f.cancel_at=variant-normal;
   struct mm_transport mm={.bus={&f,read_reg,write_reg,fence},.budget=3,.bound=1};
   assert(!mat_begin(&s,&mm,input,length,1));assert(mat_begin(&s,&mm,input,length,1)==MAT_INVALID);
   for(size_t i=0;i<length;i++)input[i]^=0xff; /* Owned copy survives caller changes. */
   int result=0;unsigned turns=0;
   while(!result){unsigned before=f.calls;result=mat_step(&s);assert(f.calls-before<=1&&++turns<normal+16);if(f.cancel_at&&f.calls==f.cancel_at)assert(result==MAT_CANCELLED);}
   if(variant|| (mode>=1&&mode<=6))assert(result<0&&mm.failed);
   else {assert(result==1&&f.commits==1&&s.commit_attempted&&f.length==length);for(size_t i=0;i<length;i++)assert(f.memory[i]==original[i]);assert(turns==normal+(mode==7?4u:0u));}
   unsigned calls=f.calls,commits=f.commits;assert(mat_step(&s)==result&&f.calls==calls&&f.commits==commits);mat_cancel(&s);assert(mat_step(&s)==result&&f.calls==calls);
   cases++;
  }
 }
 struct mat_session s={0};struct fake f={.s=&s};struct mm_transport mm={.bus={&f,read_reg,write_reg,fence},.bound=1,.budget=3};uint8_t byte[1025]={0};
 for(size_t n=0;n<=1025;n++)if(n<4||n>1024||n%4)assert(mat_begin(&s,&mm,byte,n,1)==MAT_INVALID&&!s.started&&!mm.failed);
 assert(mat_begin(&s,&mm,byte,8,0)==MAT_INVALID&&!s.started);
 assert(!f.calls);for(unsigned i=0;i<8;i++){s.bytes[i]=(uint8_t)(17+i);}
 assert(!mat_begin(&s,&mm,s.bytes,8,1));for(unsigned i=0;i<8;i++){assert(s.bytes[i]==17+i);}
 assert(!f.calls);mat_cancel(&s);assert(mat_step(&s)==MAT_CANCELLED&&!f.calls&&mm.failed);
 printf("MASTER_AUX_RESUMABLE_TX_PASS cases=%u max_callbacks_per_turn=1\n",cases);return 0;
}
