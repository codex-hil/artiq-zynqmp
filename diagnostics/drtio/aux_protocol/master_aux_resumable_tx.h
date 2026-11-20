/* SPDX-License-Identifier: LGPL-3.0-or-later */
#pragma once
#include "master_aux_mmio.h"
/* Isolated TX-only offline candidate: exactly one bus callback per step.
 * Sole link/CPU/transport owner throughout; never interleave legacy send/RX or
 * another session. Caller qualifies map/clock/reset epoch and owns admission.
 * Packet copied at begin; no borrowed caller memory across foreground turns.
 * Empty RX is a snapshot, not delayed-duplicate proof. No retry/reset/cleanup.
 * Finite callback count does not bound a single hung AXI operation.
 */
enum mat_error {MAT_INVALID=-1,MAT_IO=-2,MAT_TIMEOUT=-3,MAT_CANCELLED=-4};
struct mat_session {struct mm_transport *mm;unsigned started,phase,commit_attempted;uint32_t left;size_t size,offset;int terminal;uint8_t bytes[1024];};
static inline int mat_fail(struct mat_session *s,int error){
 if(!s)return MAT_INVALID;
 if(!s->terminal){s->terminal=error<0?error:MAT_INVALID;if(s->mm)mm_fail(s->mm);}
 return s->terminal;
}
/* Zero initialize once; started sessions never reopened, including success. */
static inline int mat_begin(struct mat_session *s,struct mm_transport *m,const uint8_t *bytes,size_t size,unsigned reviewed_epoch){
 if(!s||s->started||!mm_ready(m)||m->held||!m->bus.read||!m->bus.write||!m->bus.fence||!m->budget||!bytes||size<4||size>1024||size%4||reviewed_epoch!=1)return MAT_INVALID;
 struct mat_session candidate={.mm=m,.started=1,.left=m->budget,.size=size};
 for(size_t i=0;i<size;i++){candidate.bytes[i]=bytes[i];}
 *s=candidate;return 0;
}
static inline void mat_cancel(struct mat_session *s){if(s&&s->started&&!s->terminal)mat_fail(s,MAT_CANCELLED);}
static inline int mat_step(struct mat_session *s){
 if(!s||!s->started)return MAT_INVALID;
 if(s->terminal)return s->terminal;
 struct mm_transport *m=s->mm;if(!mm_ready(m)||m->held)return mat_fail(s,MAT_IO);
 unsigned phase=s->phase,op=0;uint32_t a=0,v=0;
 switch(phase){
  case 0:a=MM_RX_ERROR;break;
  case 1:a=MM_RX_PRESENT;break;
  case 2:case 10:a=MM_TX_BUSY;break;
  case 3:
   a=MM_TX_MEMORY+(uint32_t)s->offset;op=1;
   v=(uint32_t)s->bytes[s->offset]|((uint32_t)s->bytes[s->offset+1]<<8)|((uint32_t)s->bytes[s->offset+2]<<16)|((uint32_t)s->bytes[s->offset+3]<<24);break;
  case 4:case 7:case 9:op=2;break;
  case 5:a=MM_TX_LENGTH;v=(uint32_t)s->size;op=1;break;
  case 6:a=MM_TX_LENGTH;break;
  case 8:a=MM_TX_BUSY;v=1;op=1;s->commit_attempted=1;m->commit_attempted=1;break;
  default:return mat_fail(s,MAT_INVALID);
 }
 int error=op==0?m->bus.read(m->bus.ctx,a,&v):op==1?m->bus.write(m->bus.ctx,a,v):m->bus.fence(m->bus.ctx);
 if(s->terminal)return s->terminal; /* Synchronous cancellation wins. */
 if(error)return mat_fail(s,MAT_IO);
 if((phase==0||phase==1)&&v)return mat_fail(s,MAT_IO);
 if(phase==2||phase==10){
  if(v>1)return mat_fail(s,MAT_IO);
  if(v)return --s->left?0:mat_fail(s,MAT_TIMEOUT);
  if(phase==10){s->terminal=1;return 1;}
  s->left=m->budget;
 }
 if(phase==3){s->offset+=4;if(s->offset<s->size)return 0;}
 if(phase==6&&v!=s->size)return mat_fail(s,MAT_IO);
 s->phase++;return 0;
}
