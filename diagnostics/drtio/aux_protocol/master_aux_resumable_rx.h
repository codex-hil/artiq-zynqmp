/* SPDX-License-Identifier: LGPL-3.0-or-later */
#pragma once
#include "master_aux_mmio.h"
#include "master_ack_slot.h"
/* Isolated fixed8-byte reply RX, not generic frame/received-length support.
 * Zero-init once; sole software owner across ALL yields, no legacy RX/TX or
 * competing session. Pointer slot remains leased until attempted pop, even on
 * errors/cancel. A failed/ambiguous pop is never retried. No reset/cleanup.
 * Decoder must be strict, bounded, side-effect free; panic recovery external.
 * Max1bus callback/step (decoder-only step has0); no elapsedtime/AXI bound.
 */
enum mar_error {MAR_INVALID=-1,MAR_IO=-2,MAR_TIMEOUT=-3,MAR_CANCELLED=-4,MAR_PACKET=-5};
struct mar_session {struct mm_transport *mm;ma_fixed_decoder decode;unsigned started,phase,release_attempted;uint32_t left,pointer,kind;int decoded,terminal;uint8_t bytes[8];};
static inline int mar_fail(struct mar_session *s,int error){
 if(!s)return MAR_INVALID;
 if(!s->terminal){s->terminal=error<0?error:MAR_INVALID;if(s->mm)mm_fail(s->mm);}
 return s->terminal;
}
static inline int mar_begin(struct mar_session *s,struct mm_transport *m,ma_fixed_decoder decode,unsigned reviewed_epoch){
 if(!s||s->started||!mm_ready(m)||m->held||!m->bus.read||!m->bus.write||!m->bus.fence||!m->budget||!decode||reviewed_epoch!=1)return MAR_INVALID;
 *s=(struct mar_session){.mm=m,.decode=decode,.started=1,.left=m->budget};return 0;
}
static inline void mar_cancel(struct mar_session *s){if(s&&s->started&&!s->terminal)mar_fail(s,MAR_CANCELLED);}
static inline int mar_step(struct mar_session *s){
 if(!s||!s->started)return MAR_INVALID;
 if(s->terminal)return s->terminal;
 struct mm_transport *m=s->mm;if(!mm_ready(m))return mar_fail(s,MAR_IO);
 unsigned phase=s->phase;uint32_t a=0,v=0;unsigned op=0;
 if((phase<=2&&m->held)||(phase>=3&&phase<=11&&(!m->held||m->pointer!=s->pointer))||(phase==12&&m->held))return mar_fail(s,MAR_IO);
 if(phase==7){
  s->decoded=s->decode(s->bytes,8);
  if(s->terminal)return s->terminal;
  s->phase++;return 0; /* Invalid envelope still releases owned slot once. */
 }
 switch(phase){
  case 0:case 5:case 8:a=MM_RX_ERROR;break;
  case 1:case 10:a=MM_RX_PRESENT;break;
  case 2:case 6:case 9:a=MM_RX_POINTER;break;
  case 3:case 4:a=MM_RX_MEMORY+s->pointer*1024+(phase-3)*4;break;
  case 11:
   if(!m->held||m->pointer!=s->pointer)return mar_fail(s,MAR_IO);
   a=MM_RX_PRESENT;v=1;op=1;s->release_attempted=1;m->release_attempted=1;m->held=0;break;
  case 12:op=2;break;
  default:return mar_fail(s,MAR_INVALID);
 }
 int error=op==0?m->bus.read(m->bus.ctx,a,&v):op==1?m->bus.write(m->bus.ctx,a,v):m->bus.fence(m->bus.ctx);
 if(s->terminal)return s->terminal;
 if(error)return mar_fail(s,MAR_IO);
 if((phase==0||phase==5||phase==8)&&v)return mar_fail(s,MAR_IO);
 if(phase==1){
  if(v>1)return mar_fail(s,MAR_IO);
  if(!v){if(!--s->left)return mar_fail(s,MAR_TIMEOUT);s->phase=0;return 0;}
 }
 if(phase==2){if(v>7)return mar_fail(s,MAR_IO);s->pointer=v;m->pointer=v;m->held=1;}
 if((phase==6||phase==9)&&v!=s->pointer)return mar_fail(s,MAR_IO);
 if(phase==10&&v!=1)return mar_fail(s,MAR_IO);
 if(phase==3||phase==4){unsigned offset=(phase-3)*4;for(unsigned j=0;j<4;j++){s->bytes[offset+j]=(uint8_t)(v>>(8*j));}}
 if(phase==12){
  if(s->decoded<=0)return mar_fail(s,MAR_PACKET);
  s->kind=(uint32_t)s->decoded;s->terminal=1;return 1;
 }
 s->phase++;return 0;
}
