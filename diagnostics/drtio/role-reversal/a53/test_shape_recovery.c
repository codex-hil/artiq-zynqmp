/* SPDX-License-Identifier: LGPL-3.0-or-later */
#include <assert.h>
#include <stdio.h>
#include "shape_recovery.h"
struct model {unsigned calls,fail,writes,mode;uint32_t status,fault;};
static int rd(void*p,uint32_t a,uint32_t*v) {
 struct model*m=p;assert(a==GR_BASE||a==GR_BASE+8||a==GR_BASE+12);
 if(++m->calls==m->fail)return -1;
 *v=a==GR_BASE?GR_ID:a==GR_BASE+8?m->status:m->fault;return 0;
}
static int wr(void*p,uint32_t a,uint32_t v) {
 struct model*m=p;assert(a==GR_BASE+4&&v<=2);m->writes++;
 m->status=v==1?1:v==0?3:4;
 if(v==1&&m->mode!=1)m->fault=0;
 if(v==2&&m->mode==2)m->fault=1;
 /* Side effect may happen even when the callback reports failure. */
 return ++m->calls==m->fail?-1:0;
}
static int fence(void*p){struct model*m=p;return ++m->calls==m->fail?-1:0;}
static struct model fresh(void){return(struct model){.status=1,.fault=1};}
static struct gm_bus bus(struct model*m){return(struct gm_bus){m,rd,wr,fence};}
int main(void) {
 unsigned cases=0;struct model m=fresh();struct gm_bus b=bus(&m);
 struct gsr_result r=gsr_recover(&b,4,1,1,1);
 assert(r.error==GR_OK&&r.reset_attempted&&r.release_attempted&&r.shape_valid&&!r.shape);
 assert(m.writes==3);unsigned calls=m.calls;cases++;
 for(unsigned fail=1;fail<=calls;fail++) {
  m=fresh();m.fail=fail;b=bus(&m);r=gsr_recover(&b,4,1,1,1);
  assert(r.error==GR_IO&&m.calls==fail);cases++; /* no retry or cleanup write */
 }
 for(unsigned which=0;which<3;which++) {
  m=fresh();m.fault=0;b=bus(&m);
  r=gsr_recover(&b,4,which==0?0:1,which==1?0:1,which==2?0:1);
  assert(r.error==GR_INVALID&&!m.calls&&!m.writes);cases++;
 }
 m=fresh();m.fault=0;b=bus(&m);r=gsr_recover(&b,4,1,1,1);
 assert(r.error==GR_OK&&m.writes==3);cases++; /* zero still needs explicit reset */
 m=fresh();m.mode=1;b=bus(&m);r=gsr_recover(&b,4,1,1,1);
 assert(r.error==GSR_SHAPE_FAULT&&r.reset_attempted&&!r.release_attempted&&m.writes==1);cases++;
 m=fresh();m.mode=2;b=bus(&m);r=gsr_recover(&b,4,1,1,1);
 assert(r.error==GSR_SHAPE_FAULT&&r.release_attempted&&r.shape_valid&&r.shape==1);cases++;
 printf("SHAPE_RECOVERY_MODEL_PASS %u cases %u failurepoints\n",cases,calls);
}
