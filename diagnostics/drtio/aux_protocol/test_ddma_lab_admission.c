/* Mocked I/O adapter ordering/failure tests; LGPL-3.0-or-later. */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#define xil_printf(...) ((void)0)
#include "ddma_lab_admission.h"
struct mock {uint32_t r[18];unsigned copied,flushed,starts,delays,mode,times;uint64_t now;};
static uint32_t read_reg(void *c,uintptr_t a) {struct mock *m=c;assert(a>=DDMA_BANK && a<DDMA_BANK+72);return m->r[(a-DDMA_BANK)/4];}
static void write_reg(void *c,uintptr_t a,uint32_t v) {
 struct mock *m=c;unsigned i=(a-DDMA_BANK)/4;assert(i<18);
 if(a==DDMA_BANK+DB_START) {assert(m->copied && m->flushed);m->starts++;if(!m->mode)m->r[DB_ACCEPTED/4]++;return;}
 m->r[i]=v;
}
static int copy(void *c,uintptr_t a,const uint8_t *p,size_t n) {struct mock *m=c;assert(a==DDMA_ARENA && p && n==2048);m->copied++;return 0;}
static void flush(void *c,uintptr_t a,size_t n) {struct mock *m=c;assert(m->copied && a==DDMA_ARENA && n==2048);m->flushed++;}
static int time_read(void *c,uint64_t *t) {struct mock *m=c;m->times++;*t=(m->mode==2 && m->times>1)?8000000:m->now;return 0;}
static int ready(void *c) {(void)c;return 1;}
static void delay(void *c) {((struct mock*)c)->delays++;}
int main(void) {
 uint8_t bytes[2048]={0};
 for(unsigned test=0;test<8;test++) {
  struct mock a={0},b={0};
  if(test==1)a.now=7500000;
  if(test==2)a.mode=2;
  if(test==3)a.mode=1;
  if(test==4)a.r[DB_ACTIVE/4]=1;
  if(test==5)a.r[DB_PENDING/4]=1;
  b=a;
  struct ddma_backend original={&a,read_reg,write_reg,copy,flush,time_read,ready,delay,0};
  struct ddma_backend observed={&b,read_reg,write_reg,copy,flush,time_read,ready,delay,0};
  if(test==6){original.time=0;observed.time=0;}
  unsigned length=test==7?2047:2048;
  int x=ddma_backend_start(&original,bytes,length,8000000);
  int y=ddma_lab_admission_start(&observed,bytes,length,8000000);
  assert(x==y && original.faulted==observed.faulted);
  assert(!memcmp(&a,&b,sizeof(a)));
 }
 puts("DDMA_LAB_ADMISSION_DIFFERENTIAL_PASS success early late active pending timeout missing invalid");
}
