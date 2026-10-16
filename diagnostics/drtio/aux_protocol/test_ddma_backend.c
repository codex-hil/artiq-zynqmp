/* Mocked I/O adapter ordering/failure tests; LGPL-3.0-or-later. */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "ddma_backend.h"
struct mock {uint32_t r[18];unsigned copied,flushed,starts,delays,mode,times;};
static uint32_t read_reg(void *c,uintptr_t a) {struct mock *m=c;assert(a>=DDMA_BANK && a<DDMA_BANK+72);return m->r[(a-DDMA_BANK)/4];}
static void write_reg(void *c,uintptr_t a,uint32_t v) {
 struct mock *m=c;unsigned i=(a-DDMA_BANK)/4;assert(i<18);
 if(a==DDMA_BANK+DB_START) {assert(m->copied && m->flushed);m->starts++;if(!m->mode)m->r[DB_ACCEPTED/4]++;return;}
 m->r[i]=v;
}
static int copy(void *c,uintptr_t a,const uint8_t *p,size_t n) {struct mock *m=c;assert(a==DDMA_ARENA && p && n==2048);m->copied++;return 0;}
static void flush(void *c,uintptr_t a,size_t n) {struct mock *m=c;assert(m->copied && a==DDMA_ARENA && n==2048);m->flushed++;}
static int time_read(void *c,uint64_t *t) {struct mock *m=c;m->times++;*t=(m->mode==2 && m->times>1)?8000000:0;return 0;}
static int ready(void *c) {(void)c;return 1;}
static void delay(void *c) {((struct mock*)c)->delays++;}
int main(void) {
 uint8_t bytes[2048]={0};struct mock m={0};
 struct ddma_backend b={&m,read_reg,write_reg,copy,flush,time_read,ready,delay,0};
 assert(!ddma_backend_start(&b,bytes,sizeof(bytes),8000000));
 assert(m.starts==1 && m.copied==1 && m.flushed==1 && !b.faulted);
 assert(m.r[DB_BUDGET/4]==16 && db_read64(&b,DB_ADDRESS)==DDMA_ARENA);
 m.r[DB_ACTIVE/4]=1;assert(ddma_backend_start(&b,bytes,2048,8000000)<0 && m.starts==1);m.r[DB_ACTIVE/4]=0;
 m.r[DB_PENDING/4]=1;assert(ddma_backend_start(&b,bytes,2048,8000000)<0 && m.starts==1);m.r[DB_PENDING/4]=0;
 b.time=0;assert(ddma_backend_start(&b,bytes,2048,8000000)<0 && m.starts==1);b.time=time_read;
 assert(ddma_backend_start(&b,bytes,2047,8000000)<0);
 assert(ddma_backend_start(&b,bytes,2048,8)<0);
 memset(&m,0,sizeof(m));m.mode=2;
 assert(ddma_backend_start(&b,bytes,2048,8000000)<0 && !m.starts && m.flushed);
 memset(&m,0,sizeof(m));m.mode=1;
 assert(ddma_backend_start(&b,bytes,2048,8000000)<0 && m.starts==1 && m.delays==1000 && b.faulted);
 assert(ddma_backend_start(&b,bytes,2048,8000000)<0 && m.starts==1);
 puts("DDMA_BACKEND_OFFLINE_PASS ordering, bounds, missing-time, expired-time, timeout-latch");
}
