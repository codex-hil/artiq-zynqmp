/* SPDX-License-Identifier: LGPL-3.0-or-later */
#include "aib_backend.h"
#include "aib_session.h"
#include <assert.h>
#ifndef EXPECT_BLOCK
#define EXPECT_BLOCK 1
#endif
struct fake {uint32_t req;unsigned reads,writes;uint64_t time,delay;int mode;};
static int rd(void *v,uint32_t a,uint32_t *out) {
 struct fake *f=v;f->reads++;
 if(f->mode==3 && f->reads==9)f->time=0;
 if(f->mode==1 && f->reads==9)f->time+=f->delay; /* backend recheck after protocol deadline check */
 *out=a==0xff413030?f->req:a==0xff413040?f->req:0x19cf000f;return 0;
}
static int wr(void *v,uint32_t a,uint32_t value) {
 struct fake *f=v;assert(a==0xff413030);f->writes++;f->req=value;
 if(f->mode==2)f->time+=f->delay; /* submitted write completes late; never undo */
 return f->mode==5 ? -2 : 0;
}
static int tick(void *v,uint64_t *t) {struct fake *f=v;if(f->mode==4 && f->reads>=10)return -1;*t=f->time++;return 0;}
int main(void) {
 for(unsigned variant=0;variant<3;variant++) for(int mode=0;mode<6;mode++) {
  uint64_t timeout=variant==2 ? (UINT64_C(1)<<32)+10 : 10;
  struct fake f={.req=0xc00000,.mode=mode,.time=variant ? UINT64_C(0x1234567800000000) : 0,.delay=variant==2 ? (UINT64_C(1)<<32)+100 : 100};struct aib_transport t={&f,rd,wr,tick};struct aib_backend b={0};
  assert(aib_backend_prepare(&b,&t,0x30000)==0);
  struct aib_session s={0};assert(!aib_session_arm(&s,7,9,1));
  struct aib_receipt r=aib_session_execute(&s,7,9,1,&b.io,0x30000,3,timeout);
  assert(r.accepted && s.consumed && !r.result.destructive_test_allowed);
  if(mode==0)assert(f.writes==1 && r.result.status==AIB_DRAIN_OBSERVED);
  if(mode==1)assert(f.writes==(EXPECT_BLOCK?0U:1U) && r.result.status==AIB_TIMEOUT);
  if(mode==2)assert(f.writes==1 && r.result.status==AIB_TIMEOUT && f.req==0xc30000);
  if(mode==3)assert(!f.writes && r.result.status==AIB_CLOCK_ERROR);
  if(mode==4)assert(!f.writes && r.result.status==AIB_IO_UNCERTAIN);
  if(mode==5)assert(f.writes==1 && r.result.status==AIB_IO_UNCERTAIN);
  unsigned reads=f.reads,writes=f.writes;
  assert(!aib_session_execute(&s,7,9,1,&b.io,0x30000,3,timeout).accepted);
  assert(f.reads==reads && f.writes==writes);
 }
 return 0;
}
