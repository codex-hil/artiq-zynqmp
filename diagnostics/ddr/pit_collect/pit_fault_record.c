/* SPDX-License-Identifier: LGPL-3.0-or-later */
#include "pit_fault_record.h"
#define FAULT_MAGIC UINT32_C(0x50465831)
static int valid_words(const volatile uint32_t *w)
{
 unsigned i;
 if(w[0]!=1||w[1]!=FAULT_MAGIC||w[2]!=1||(w[3]!=1&&w[3]!=2)||(w[4]&~15u))return 0;
 for(i=0;i<4;i++)if(!(w[4]&(1u<<i))&&w[5+i])return 0;
 for(i=9;i<16;i++)if(w[i])return 0;
 return 1;
}
int pit_fault_format(uint32_t out[16],uint32_t route,uint32_t valid,const uint32_t registers[4])
{
 volatile uint32_t staged[16];
 unsigned i;
 if(!out||!registers||((uintptr_t)out&3u)||((uintptr_t)registers&3u)||
    (route!=1&&route!=2)||(valid&~15u))return -1;
 for(i=0;i<16;i++)if(((const volatile uint32_t *)out)[i])return -1;
 for(i=0;i<16;i++)staged[i]=0;
 staged[0]=1;staged[1]=FAULT_MAGIC;staged[2]=1;staged[3]=route;staged[4]=valid;
 for(i=0;i<4;i++){
  uint32_t value=((const volatile uint32_t *)registers)[i];
  if(!(valid&(1u<<i))&&value)return -1;
  staged[5+i]=value;
 }
 for(i=0;i<16;i++)((volatile uint32_t *)out)[i]=staged[i];
 return 0;
}
enum pit_publish_status pit_fault_publish(struct pit_attempt *attempt,const uint32_t words[16],
 pit_write_fn write,pit_barrier_fn barrier,void *ctx)
{
 volatile uint32_t staged[16];
 unsigned i;
 if(!attempt||attempt->consumed||!words||((uintptr_t)words&3u)||!write||!barrier)
  return PIT_PUBLISH_REJECTED;
 for(i=0;i<16;i++)staged[i]=((const volatile uint32_t *)words)[i];
 if(!valid_words(staged))return PIT_PUBLISH_REJECTED;
 attempt->consumed=1;
 if(write(ctx,0,0)||barrier(ctx))return PIT_VISIBILITY_UNKNOWN;
 for(i=1;i<16;i++)if(write(ctx,i*4,staged[i]))return PIT_VISIBILITY_UNKNOWN;
 if(barrier(ctx)||write(ctx,0,1))return PIT_VISIBILITY_UNKNOWN;
 return PIT_CALLBACKS_RETURNED_OFFLINE;
}
