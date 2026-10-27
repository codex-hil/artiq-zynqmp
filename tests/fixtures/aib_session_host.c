/* SPDX-License-Identifier: LGPL-3.0-or-later */
#include "aib_session.h"
#include <assert.h>
struct fake {unsigned reads,writes;uint32_t req;uint64_t ticks;int fail;
 struct aib_session *session;const struct aib_io *io;};
static int rd(void *v,enum aib_reg reg,uint32_t *out) {
 struct fake *f=v;f->reads++;
 *out=reg==AIB_REQ ? f->req : reg==AIB_ACK ? f->req : 0x19cf000f;
 return 0;
}
static int wr(void *v,uint32_t req) {
 struct fake *f=v;f->writes++;f->req=req;
 struct aib_receipt nested=aib_session_execute(f->session,7,9,1,f->io,0x30000,3,100);
 assert(!nested.accepted);assert(f->writes==1);return f->fail;
}
static int tick(void *v,uint64_t *n) {struct fake *f=v;*n=f->ticks++;return 0;}
int main(void) {
 for(int fail=0;fail<=1;fail++) {
  struct aib_session s={0};struct fake f={.req=0xc00000,.fail=fail,.session=&s};
  struct aib_io io={&f,rd,wr,tick};f.io=&io;
  assert(aib_session_arm(&s,7,9,1)==0);
  assert(aib_session_arm(&s,7,10,2)==-1);
  const uint64_t bad[3][3]={{8,9,1},{7,8,1},{7,9,2}};
  for(unsigned i=0;i<3;i++) {
   struct aib_receipt r=aib_session_execute(&s,bad[i][0],bad[i][1],bad[i][2],&io,0x30000,3,100);
   assert(!r.accepted && !f.reads && !f.writes && !s.consumed);
  }
  struct aib_receipt r=aib_session_execute(&s,7,9,1,&io,0x30000,3,100);
  assert(r.accepted && r.boot==7 && r.nonce==9 && r.sequence==1);
  assert(r.result.status==(fail ? AIB_IO_UNCERTAIN : AIB_DRAIN_OBSERVED));
  assert(s.consumed && f.writes==1 && f.req==0xc30000 && !r.result.destructive_test_allowed);
  unsigned reads=f.reads;
  r=aib_session_execute(&s,7,9,1,&io,0x30000,3,100);
  assert(!r.accepted && f.reads==reads && f.writes==1);
  assert(aib_session_arm(&s,7,10,2)==-1);
 }
 struct aib_session s={0};
 assert(aib_session_arm(&s,0,1,1)==-1);
 assert(aib_session_arm(&s,1,0,1)==-1);
 assert(aib_session_arm(&s,1,1,0)==-1);
 assert(aib_session_arm(0,1,1,1)==-1);
 assert(aib_session_arm(&s,1,1,1)==0);
 struct aib_receipt r=aib_session_execute(&s,1,1,1,0,0x30000,3,100);
 assert(r.accepted && s.consumed && r.result.status==AIB_REJECTED);
 assert(!aib_session_execute(&s,1,1,1,0,0x30000,3,100).accepted);
 return 0;
}
