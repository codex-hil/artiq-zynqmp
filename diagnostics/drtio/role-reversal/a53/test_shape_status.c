/* SPDX-License-Identifier: LGPL-3.0-or-later */
#include <assert.h>
#include <stdio.h>
#include "reset_driver.h"
struct model {unsigned calls,fail;uint32_t identity,fault;};
static int rd(void *p,uint32_t a,uint32_t *v) {
 struct model*m=p;assert(a==GR_BASE||a==GR_BASE+12);
 m->calls++;if(m->calls==m->fail)return -1;
 *v=a==GR_BASE?m->identity:m->fault;return 0;
}
static struct model fresh(void){return(struct model){.identity=GR_ID};}
int main(void) {
 unsigned cases=0;uint32_t out;int rc;struct model m;struct gm_bus b;
 for(unsigned fault=0;fault<2;fault++) {
  m=fresh();m.fault=fault;b=(struct gm_bus){.context=&m,.read=rd};out=99;
  rc=gr_shape_status(&b,1,&out);assert(rc==GR_OK&&out==fault&&m.calls==2);cases++;
 }
 for(unsigned failure=1;failure<=2;failure++) {
  m=fresh();m.fail=failure;b=(struct gm_bus){.context=&m,.read=rd};out=99;
  rc=gr_shape_status(&b,1,&out);assert(rc==GR_IO&&out==99&&m.calls==failure);cases++;
 }
 for(unsigned capability=0;capability<=2;capability+=2) {
  m=fresh();b=(struct gm_bus){.context=&m,.read=rd};out=99;
  rc=gr_shape_status(&b,capability,&out);assert(rc==GR_INVALID&&out==99&&!m.calls);cases++;
 }
 m=fresh();m.identity=0;b=(struct gm_bus){.context=&m,.read=rd};out=99;
 rc=gr_shape_status(&b,1,&out);assert(rc==GR_PROFILE&&out==99&&m.calls==1);cases++;
 for(uint32_t value=2;value<=8;value*=2) {
  m=fresh();m.fault=value;b=(struct gm_bus){.context=&m,.read=rd};out=99;
  rc=gr_shape_status(&b,1,&out);assert(rc==GR_IO&&out==99&&m.calls==2);cases++;
 }
 m=fresh();b=(struct gm_bus){.context=&m,.read=rd};
 assert(gr_shape_status(&b,1,NULL)==GR_INVALID&&!m.calls);cases++;
 out=99;assert(gr_shape_status(NULL,1,&out)==GR_INVALID&&out==99);cases++;
 b.read=NULL;assert(gr_shape_status(&b,1,&out)==GR_INVALID&&out==99);cases++;
 printf("SHAPE_STATUS_MODEL_PASS %u cases\n",cases);
}
