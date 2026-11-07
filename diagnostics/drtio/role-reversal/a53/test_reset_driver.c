/* SPDX-License-Identifier: LGPL-3.0-or-later */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "reset_driver.h"
struct model {unsigned calls,fail,writes,identity,status,mode;};
static int rd(void *p,uint32_t a,uint32_t *v) {
 struct model *m=p;assert(a==GR_BASE||a==GR_BASE+8);
 m->calls++;if(m->calls==m->fail)return -1;
 *v=a==GR_BASE?m->identity:m->status;return 0;
}
static int wr(void *p,uint32_t a,uint32_t v) {
 struct model *m=p;assert(a==GR_BASE+4);assert(v<=2);m->writes++;
 /* Side effect precedes injected error: callbacks cannot imply rollback. */
 if(!m->mode)m->status=v==1?1:v==0?3:4;
 m->calls++;return m->calls==m->fail?-1:0;
}
static int fence(void *p){struct model*m=p;return ++m->calls==m->fail?-1:0;}
static struct gm_bus bus(struct model*m){return (struct gm_bus){m,rd,wr,fence};}
static struct model fresh(void){return (struct model){.identity=GR_ID,.status=1};}
int main(void) {
 unsigned cases=0;
 for(unsigned release=0;release<2;release++) {
  struct model m=fresh();struct gm_bus b=bus(&m);
  struct gr_result r=release?gr_release_reset(&b,4,1):gr_assert_reset(&b,4);
  assert(r.error==GR_OK);unsigned calls=m.calls;cases++;
  for(unsigned point=1;point<=calls;point++) {
   m=fresh();m.fail=point;b=bus(&m);
   r=release?gr_release_reset(&b,4,1):gr_assert_reset(&b,4);
   assert(r.error==GR_IO);assert(m.calls==point); /* no automatic retry */
   if(release&&point>=5)assert(r.release_attempted);
   if(!release&&point>=2)assert(r.reset_attempted);
   cases++;
  }
 }
 struct model m=fresh();struct gm_bus b=bus(&m);struct gr_result r;
 r=gr_release_reset(&b,4,0);assert(r.error==GR_INVALID&&!m.calls);cases++;
 r=gr_assert_reset(&b,0);assert(r.error==GR_INVALID&&!m.calls);cases++;
 r=gr_assert_reset(&b,1025);assert(r.error==GR_INVALID&&!m.calls);cases++;
 m.identity=0;r=gr_assert_reset(&b,4);assert(r.error==GR_PROFILE&&!m.writes);cases++;
 m=fresh();m.mode=1;m.status=0;b=bus(&m);r=gr_assert_reset(&b,4);
 assert(r.error==GR_TIMEOUT&&r.status_reads==4&&m.writes==1);cases++;
 m=fresh();m.mode=1;m.status=1;b=bus(&m);r=gr_release_reset(&b,4,1);
 assert(r.error==GR_TIMEOUT&&!r.release_attempted&&m.writes==1);cases++;
 m=fresh();m.mode=1;m.status=8;b=bus(&m);r=gr_assert_reset(&b,4);
 assert(r.error==GR_IO&&r.status_reads==1);cases++;
 printf("RESET_DRIVER_MODEL_PASS %u cases\n",cases);
}
