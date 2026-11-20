/* SPDX-License-Identifier: LGPL-3.0-or-later */
#pragma once
#include "master_aux_mmio.h"
#define MRT_RX_UP UINT32_C(0xa0001000)
#define MRT_ERROR UINT32_C(0xa0001038)
#define MRT_SET_TIME UINT32_C(0xa000103c)
#define MRT_FORCE UINT32_C(0xa0001044)
#define MRT_DEST UINT32_C(0xa0001048)
#define MRT_BUFFER UINT32_C(0xa000104c)
#define MRT_SPACE UINT32_C(0xa0001050)
#define MRT_COUNT UINT32_C(0xa0001054)
#define MRT_WAIT UINT32_C(0xa0001058)
/* Callback-only fixed-destination1 candidate. Same reviewed profile/sole CRI
 * owner/live epoch prerequisites as mm_transport. No automatic cleanup/reset/
 * retransmission on error; failed force write may have changed hardware state.
 * SET_TIME success only local transmit completion, still needs remote TSCAck.
 */
struct mrt_setup {struct mm_transport *mm;unsigned time_attempted,force_attempted,request_attempted,unforce_attempted;uint32_t credits;};
static inline int mrt_live(struct mm_transport *m){
 uint32_t up,error;if(mm_read(m,MRT_RX_UP,&up)||up!=1||mm_read(m,MRT_ERROR,&error)||error)return mm_fail(m);
 return 0;
}
static inline int mrt_write(struct mm_transport *m,uint32_t a,uint32_t v){
 if(m->bus.write(m->bus.ctx,a,v)||m->bus.fence(m->bus.ctx))return mm_fail(m);
 return 0;
}
static inline int mrt_set_time_once(struct mrt_setup *r){
 if(!r||!mm_ready(r->mm)||r->time_attempted)return -1;
 struct mm_transport *m=r->mm;uint32_t busy;
 if(mrt_live(m)||mm_read(m,MRT_SET_TIME,&busy)||busy)return mm_fail(m);
 r->time_attempted=1;if(mrt_write(m,MRT_SET_TIME,1))return -1;
 for(uint32_t i=0;i<m->budget;i++){
  if(mm_read(m,MRT_SET_TIME,&busy)||busy>1)return mm_fail(m);
  if(!busy)return mrt_live(m);
 }
 return mm_fail(m);
}
static inline int mrt_buffer_once(struct mrt_setup *r){
 if(!r||!mm_ready(r->mm)||r->force_attempted||r->request_attempted)return -1;
 struct mm_transport *m=r->mm;uint32_t force,busy,before,count,space;
 if(mrt_live(m)||mm_read(m,MRT_FORCE,&force)||force||mm_read(m,MRT_WAIT,&busy)||busy||mm_read(m,MRT_COUNT,&before))return mm_fail(m);
 if(mrt_write(m,MRT_DEST,1))return -1;
 r->force_attempted=1;if(mrt_write(m,MRT_FORCE,1))return -1;
 if(mm_read(m,MRT_FORCE,&force)||force!=1)return mm_fail(m);
 r->request_attempted=1;if(mrt_write(m,MRT_BUFFER,1))return -1;
 for(uint32_t i=0;i<m->budget;i++){
  if(mm_read(m,MRT_WAIT,&busy)||busy>1||mm_read(m,MRT_COUNT,&count))return mm_fail(m);
  uint32_t delta=count-before;
  /* Gateware itself retries zero-space replies; this strict candidate refuses
   * more than one observed request, rather than hiding those retries. */
  if(delta>1)return mm_fail(m);
  if(!busy&&delta==1){
   if(mrt_live(m)||mm_read(m,MRT_SPACE,&space)||!space||space>65535)return mm_fail(m);
   r->unforce_attempted=1;if(mrt_write(m,MRT_FORCE,0))return -1;
   if(mm_read(m,MRT_FORCE,&force)||force)return mm_fail(m);
   r->credits=space;return 0;
  }
 }
 return mm_fail(m);
}
