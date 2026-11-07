/* LGPL-3.0-or-later. Supplied-word MMIO model, never real hardware. */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "master_driver.h"
struct event {char kind;uint32_t address,value;};
struct model {struct event e[2048];unsigned n,fail,commits,status_index;uint32_t wrong,owner,link,status[8];};
static unsigned cases;
static int step(struct model *m,char k,uint32_t a,uint32_t v) {
 assert(m->n<2048);m->e[m->n++]=(struct event){k,a,v};return m->fail==m->n;
}
static int rd(void *p,uint32_t a,uint32_t *v) {
 struct model *m=p;if(step(m,'R',a,0))return -1;
 if(a==GM_PROFILE_IDENTITY)*v=m->wrong==1?0:GM_IDENTITY;
 else if(a==GM_PROFILE_FINE_WIDTH)*v=m->wrong==2?0:3;
 else if(a==GM_PROFILE_COARSE_HZ)*v=m->wrong==3?1:125000000;
 else if(a==GM_ROUTING_SELECTED)*v=m->owner;
 else if(a==GM_MASTER_RX_UP)*v=m->link;
 else {assert(a==GM_KERNEL_O_STATUS);assert(m->status_index<8);*v=m->status[m->status_index++];}
 return 0;
}
static int wr(void *p,uint32_t a,uint32_t v) {
 struct model *m=p;
 /* A bus error may be returned after the committing write took effect. */
 if(a==GM_KERNEL_O_DATA+60)m->commits++;
 return step(m,'W',a,v)?-1:0;
}
static int fence(void *p) {return step(p,'F',0,0)?-1:0;}
static struct model fresh(void) {struct model m;memset(&m,0,sizeof(m));m.link=1;return m;}
static struct gm_result execute(struct model *m,uint32_t dest,uint32_t polls) {
 struct gm_bus b={m,rd,wr,fence};cases++;return gm_schedule(&b,dest,0x1234,UINT64_C(0x1122334455667788),0xa5,polls);
}
int main(void) {
 struct model m=fresh();struct gm_result r=execute(&m,1,4);
 assert(r.error==GM_OK&&r.commit_attempted==1&&r.status_reads==1&&m.n==13&&m.commits==1);
 assert(m.e[5].kind=='W'&&m.e[5].address==GM_KERNEL_TARGET&&m.e[5].value==0x01123400);
 assert(m.e[6].kind=='F');assert(m.e[7].address==GM_KERNEL_NOW&&m.e[7].value==0x11223344);
 assert(m.e[8].address==GM_KERNEL_NOW+4&&m.e[8].value==0x55667788&&m.e[9].kind=='F');
 assert(m.e[10].address==GM_KERNEL_O_DATA+60&&m.e[10].value==0xa5&&m.e[11].kind=='F');
 for(unsigned fault=1;fault<=13;fault++) {
  m=fresh();m.fail=fault;r=execute(&m,1,4);assert(r.error==GM_IO&&m.n==fault);
  assert(r.commit_attempted==(fault>=11));assert(m.commits==(fault>=11));
 }
 for(unsigned wrong=1;wrong<=3;wrong++) {
  m=fresh();m.wrong=wrong;r=execute(&m,1,4);assert(r.error==GM_PROFILE&&m.n==wrong&&!m.commits&&!r.commit_attempted);
 }
 m=fresh();m.owner=1;r=execute(&m,1,4);assert(r.error==GM_OWNER&&m.n==4&&!m.commits);
 m=fresh();m.link=0;r=execute(&m,1,4);assert(r.error==GM_UNREACHABLE&&m.n==5&&!m.commits);
 for(unsigned i=0;i<3;i++) {m=fresh();r=execute(&m,i==0?2:1,i==1?0:i==2?1025:4);assert(r.error==GM_INVALID&&m.n==0);}
 m=fresh();m.status[0]=1;m.status[1]=1;r=execute(&m,1,2);assert(r.error==GM_TIMEOUT&&r.status_reads==2&&m.commits==1);
 for(unsigned status=2;status<=8;status*=2) {
  m=fresh();m.status[0]=status;r=execute(&m,1,4);
  assert(r.error==(status==2?GM_UNDERFLOW:status==4?GM_UNREACHABLE:GM_IO));assert(r.status_reads==1&&m.commits==1);
 }
 m=fresh();m.link=0;r=execute(&m,0,4);assert(r.error==GM_OK&&m.n==12&&m.e[4].kind=='W');
 printf("GM_HOST_MODEL_PASS cases=%u fault_stages=13 no_retry_and_commit_uncertainty_checked\n",cases);return 0;
}
