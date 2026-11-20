/* SPDX-License-Identifier: LGPL-3.0-or-later */
#include <assert.h>
#include <stdio.h>
#include "master_rt_setup.h"
struct rt_fake {unsigned calls,fail_at,mode,timewrites,requests,forcewrites;uint32_t force,count;};
static int rt_fault(struct rt_fake *f){return ++f->calls==f->fail_at;}
static int rt_read(void *ctx,uint32_t a,uint32_t *v){
 struct rt_fake *f=ctx;if(rt_fault(f))return -1;
 if(a==0xa0000800)*v=0x47534d31;else if(a==0xa0000804)*v=3;else if(a==0xa0000808)*v=125000000;
 else if(a==MRT_RX_UP)*v=f->mode==1?0:1;
 else if(a==MRT_ERROR)*v=(f->mode==2||(f->mode==7&&f->requests))?4:0;
 else if(a==MRT_SET_TIME)*v=f->mode==3&&f->timewrites?1:0;
 else if(a==MRT_FORCE)*v=f->force;
 else if(a==MRT_WAIT)*v=f->mode==4&&f->requests?1:0;
 else if(a==MRT_COUNT)*v=f->count;
 else if(a==MRT_SPACE)*v=f->mode==5?0:16;
 else assert(0);
 return 0;
}
static int rt_write(void *ctx,uint32_t a,uint32_t v){
 struct rt_fake *f=ctx;
 if(a==MRT_SET_TIME){assert(v==1);f->timewrites++;}
 else if(a==MRT_FORCE){f->force=v;f->forcewrites++;}
 else if(a==MRT_BUFFER){assert(v==1&&f->force==1);f->requests++;f->count+=f->mode==6?2:1;}
 else assert(a==MRT_DEST&&v==1);
 return rt_fault(f)?-1:0;
}
static int rt_fence(void *ctx){return rt_fault(ctx)?-1:0;}
static unsigned run(unsigned which,unsigned fault,unsigned mode){
 struct rt_fake f={.fail_at=fault,.mode=mode,.count=0xffffffff};struct mm_transport m;
 struct mm_bus bus={&f,rt_read,rt_write,rt_fence};struct mrt_setup r={.mm=&m};
 int result=mm_bind(&m,&bus,3,1);if(!result)result=which?mrt_buffer_once(&r):mrt_set_time_once(&r);
 if(!fault&&!mode){assert(result==0);if(which)assert(r.credits==16&&f.requests==1&&f.forcewrites==2&&!f.force);else assert(f.timewrites==1);}
 else assert(result==-1&&m.failed);
 unsigned calls=f.calls;assert((which?mrt_buffer_once(&r):mrt_set_time_once(&r))==-1&&f.calls==calls);
 assert(f.timewrites<=1&&f.requests<=1&&f.forcewrites<=2);return calls;
}
int main(void){
 unsigned cases=0;
 for(unsigned which=0;which<2;which++){
  unsigned n=run(which,0,0);cases++;
  for(unsigned f=1;f<=n;f++){run(which,f,0);cases++;}
  run(which,0,1);run(which,0,2);cases+=2;
  if(!which){run(0,0,3);cases++;}else for(unsigned mode=4;mode<=7;mode++){run(1,0,mode);cases++;}
 }
 printf("MASTER_RT_SETUP_PASS scenarios=%u\n",cases);return 0;
}
