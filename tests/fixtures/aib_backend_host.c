/* SPDX-License-Identifier: LGPL-3.0-or-later */
#include "aib_backend.h"
#include "aib_session.h"
#include <assert.h>
struct fake {uint32_t req,type,ack;unsigned writes,reads;uint64_t tick;int fail_write;};
static int read32(void *v,uint32_t a,uint32_t *out) {
 struct fake *f=v;f->reads++;assert(a==0xff413030 || a==0xff413038 || a==0xff413040);
 *out=a==0xff413030?f->req:a==0xff413038?f->type:f->ack;return 0;
}
static int write32(void *v,uint32_t a,uint32_t value) {
 struct fake *f=v;assert(a==0xff413030 && value==0xc30000);
 f->writes++;f->req=value;f->ack=value;return f->fail_write;
}
static int ticks(void *v,uint64_t *out) {struct fake *f=v;*out=f->tick++;return 0;}
int main(void) {
 for(unsigned mode=0;mode<5;mode++) {
  struct fake f={.req=0xc00000,.type=0x19cf000f,.ack=0xc00000,.fail_write=mode==4};
  struct aib_transport t={&f,read32,write32,ticks};struct aib_backend b={0};
  assert(aib_backend_prepare(&b,&t,0x30000)==0 && f.writes==0);
  assert(aib_backend_prepare(&b,&t,0x30000)==-1);
  uint32_t v;unsigned n=f.reads;
  assert(b.io.read(b.io.ctx,(enum aib_reg)99,&v)==-1 && f.reads==n);
  if(mode==1)f.req=0;
  if(mode==2)f.type^=1;
  if(mode==3) {
   assert(b.io.write_request(b.io.ctx,0)==-1 && f.writes==0);
   assert(b.io.write_request(b.io.ctx,0xc30000)==-1 && f.writes==0);continue;
  }
  struct aib_session s={0};assert(aib_session_arm(&s,7,9,1)==0);
  struct aib_receipt r=aib_session_execute(&s,7,9,1,&b.io,0x30000,3,100);
  assert(r.accepted && !r.result.destructive_test_allowed);
  if(mode==0)assert(r.result.status==AIB_DRAIN_OBSERVED && f.writes==1);
  if(mode==1 || mode==2)assert(r.result.status==AIB_IO_UNCERTAIN && f.writes==0);
  if(mode==4)assert(r.result.status==AIB_IO_UNCERTAIN && f.writes==1);
  assert(b.io.write_request(b.io.ctx,0xc30000)==-1); /* no retry/clear */
 }
 struct fake f={.req=0xc10000,.type=0x19cf000f};
 struct aib_transport t={&f,read32,write32,ticks};struct aib_backend b={0};
 assert(aib_backend_prepare(&b,&t,0x30000)==-1 && !b.ready && !f.writes);
 assert(aib_backend_prepare(&b,&t,0x30000)==-1);
 return 0;
}
