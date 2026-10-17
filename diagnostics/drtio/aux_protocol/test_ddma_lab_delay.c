/* Arming refusal and exact-write proof, mocked MMIO. LGPL-3.0-or-later. */
#include <assert.h>
#include <stdio.h>
#include "ddma_lab_delay.h"
struct mock {unsigned regs[32],writes,refuse;};
static uint32_t read_reg(void *p,uintptr_t a) {
 struct mock *m=p;assert(a>=DDMA_BANK && a<DDMA_BANK+128);return m->regs[(a-DDMA_BANK)/4];
}
static void write_reg(void *p,uintptr_t a,uint32_t v) {
 struct mock *m=p;assert(a==DDMA_BANK+DB_LAB_ARM && v==1);m->writes++;
 if(!m->refuse)m->regs[DB_LAB_ARMED/4]=1;
}
int main(void) {
 unsigned blocked[]={DB_ACTIVE,DB_PENDING,DB_LAB_ARMED,DB_LAB_HOLDING,
 DB_LAB_TRIGGERS,DB_LAB_REJECTED,DB_LAB_ARM_REJECTED};
 for(unsigned i=0;i<sizeof(blocked)/sizeof(*blocked);i++) {
  struct mock m={0};m.regs[DB_LAB_CYCLES/4]=250000;m.regs[blocked[i]/4]=1;
  struct ddma_backend b={.context=&m,.read=read_reg,.write=write_reg};
  assert(ddma_lab_arm(&b,1,250000)<0 && !m.writes);
 }
 struct mock m={0};m.regs[DB_LAB_CYCLES/4]=250000;
 struct ddma_backend b={.context=&m,.read=read_reg,.write=write_reg};
 assert(ddma_lab_arm(&b,0,250000)<0 && !m.writes);
 assert(ddma_lab_arm(&b,1,200000)<0 && !m.writes);
 b.faulted=1;assert(ddma_lab_arm(&b,1,250000)<0 && !m.writes);b.faulted=0;
 m.refuse=1;assert(ddma_lab_arm(&b,1,250000)<0 && m.writes==1);
 m.refuse=0;assert(!ddma_lab_arm(&b,1,250000) && m.writes==2);
 assert(ddma_lab_arm(&b,1,250000)<0 && m.writes==2);
 puts("DDMA_LAB_DELAY_ARM_OFFLINE_PASS exact arm-only write; unsafe states refused");
}
