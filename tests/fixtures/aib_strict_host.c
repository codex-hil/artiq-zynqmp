/* SPDX-License-Identifier: LGPL-3.0-or-later */
#include "aib_strict.h"
#include <assert.h>
#include <string.h>
struct fake {uint32_t req,type,writes,reads;int mode;uint64_t tick;};
static int rd(void *v,enum aib_reg reg,uint32_t *out) {
 struct fake *f=v;f->reads++;
 if(f->mode==4 && f->writes)return -1;
 if(f->mode==9 && reg==AIB_REQ && f->reads%4==0){*out=f->req^1;return 0;}
 if(reg==AIB_REQ)*out=(f->mode==5 && f->writes) ? 0x30000 : f->req;
 else if(reg==AIB_TYPE)*out=f->type+((f->mode==6 && f->writes)?1:0);
 else *out=f->writes ? (f->mode==1 ? 0xc10000 : f->mode==2 ? 0xc00000 : 0xc30000) : (f->mode==7 ? 0xc10000 : 0xc00000);
 return 0;
}
static int wr(void *v,uint32_t n) {struct fake *f=v;f->writes++;f->req=n;return f->mode==3 ? -1 : 0;}
static int ticks(void *v,uint64_t *n) {struct fake *f=v;*n=f->tick++;if(f->mode==8 && f->writes)*n=0;return 0;}
static struct aib_result run(int mode,uint64_t timeout) {
 struct fake f={.req=0xc00000,.type=0x19cf000f,.mode=mode};
 struct aib_io io={&f,rd,wr,ticks};struct aib_result r=aib_strict_hold(&io,0x30000,3,timeout);
 assert(!r.destructive_test_allowed);assert(f.writes<=1);
 if(f.writes)assert(f.req==0xc30000); /* no automatic release, even failure */
 if(mode==7)assert(!f.writes);
 return r;
}
int main(void) {
 struct aib_result r=run(0,100);assert(r.status==AIB_DRAIN_OBSERVED && r.polls==1);
 r=run(1,100);assert(r.status==AIB_TIMEOUT && r.polls==3);
 r=run(2,100);assert(r.status==AIB_TIMEOUT && r.polls==3);
 assert(run(3,100).status==AIB_IO_UNCERTAIN);
 assert(run(4,100).status==AIB_IO_UNCERTAIN);
 assert(run(5,100).status==AIB_CHANGED);
 assert(run(6,100).status==AIB_CHANGED);
 assert(run(7,100).status==AIB_REJECTED);
 assert(run(8,100).status==AIB_CLOCK_ERROR);
 assert(run(9,100).status==AIB_CHANGED);
 assert(run(0,1).write_attempted==0);
 assert(run(0,3).status==AIB_TIMEOUT); /* deadline beats an ACK */
 assert(aib_strict_hold(0,0x30000,3,10).status==AIB_REJECTED);
 struct fake f={0};struct aib_io io={&f,rd,wr,ticks};
 assert(aib_strict_hold(&io,0x4000000,3,10).status==AIB_REJECTED);
 assert(aib_strict_hold(&io,0,3,10).status==AIB_REJECTED);
 assert(aib_strict_hold(&io,0x30000,0,10).status==AIB_REJECTED);
 assert(!f.reads && !f.writes);
 return 0;
}
