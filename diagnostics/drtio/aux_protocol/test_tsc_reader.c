/* Host mocked ordered snapshot tests; LGPL-3.0-or-later. */
#include <assert.h>
#include <stdio.h>
#include "tsc_reader.h"
struct mock {unsigned requests,polls,mode,times;};
static uint32_t read_reg(void *c,uintptr_t a) {
 struct mock *m=c;
 if(a==TS_LOAD)return m->mode==3 && m->requests?2:1;
 if(a==TS_BUSY) return m->mode==1 && m->requests?1:0;
 if(a==TS_VALID)return m->requests!=0;
 if(a==TS_VALUE)return m->mode==5?0x7fffffff:1;
 if(a==TS_VALUE+4)return m->mode==5?0xffffffff:8;
 assert(0);return 0;
}
static void write_reg(void *c,uintptr_t a,uint32_t v) {assert(a==TS_REQUEST && v==1);((struct mock*)c)->requests++;}
static int time_read(void *c,uint64_t *v) {struct mock *m=c;*v=m->times++?(m->mode==2?200001:1010):10;return 0;}
static int ready(void *c) {struct mock *m=c;return !(m->mode==4 && m->requests);}
static void delay(void *c) {((struct mock*)c)->polls++;}
int main(void) {
 struct mock m={0};struct tsc_reader r={&m,read_reg,write_reg,time_read,ready,delay};uint64_t out=0;
 assert(!tsc_read_upper(&r,&out));assert(out==((uint64_t)1<<32)+8+3000);
 for(unsigned mode=1;mode<=5;mode++) {
  m=(struct mock){0};m.mode=mode;out=123;
  assert(tsc_read_upper(&r,&out)<0 && out==123);
  if(mode==1)assert(m.polls==100);
 }
 puts("TSC_READER_OFFLINE_PASS age, timeout, epoch, readiness, signed-overflow");
}
