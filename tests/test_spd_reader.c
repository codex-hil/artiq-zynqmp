/* SPDX-License-Identifier: LGPL-3.0-or-later */
#include <assert.h>
#include <stdio.h>
#include "../diagnostics/ddr/spd_reader.h"
struct fake {int starts, fail_begin, fail_poll, busy_at, pending, mismatch;};
static int begin(void *ctx,enum spd_op op,unsigned address,uint8_t *p,unsigned n) {
 struct fake *f=ctx;int i=++f->starts;
 assert((op==SPD_LOWER_PAGE && address==0x36 && n==1 && *p==0) ||
        (op==SPD_OFFSET && address==0x51 && n==1 && *p==0) ||
        (op==SPD_READ && address==0x51 && n==128));
 if(op==SPD_READ) for(unsigned k=0;k<n;k++) p[k]=(uint8_t)(k+(f->mismatch && i==5));
 return i==f->fail_begin?-1:0;
}
static int poll(void *ctx) {struct fake *f=ctx;return f->pending?0:(f->starts==f->fail_poll?-1:1);}
static int idle(void *ctx) {struct fake *f=ctx;return f->starts==f->busy_at?0:1;}
static struct spd_transport transport(struct fake *f) {return (struct spd_transport){f,begin,poll,idle};}
static void run(struct spd_reader *r) {for(unsigned i=1;i<30050 && !r->stopped;i++) spd_reader_tick(r,r->last_now+1);assert(r->stopped);}
int main(void) {
 struct fake f={.busy_at=-1};struct spd_reader r;
 spd_reader_init(&r,transport(&f),0,0);assert(r.result==SPD_NOT_ADMITTED && f.starts==0);
 spd_reader_init(&r,transport(&f),0,1);run(&r);assert(r.result==SPD_PASS && r.page_restored && f.starts==6);
 for(int i=1;i<=6;i++) {
  f=(struct fake){.busy_at=-1,.fail_begin=i};spd_reader_init(&r,transport(&f),0,1);run(&r);
  assert(r.result==SPD_IO_ERROR);assert(f.starts<=7);assert(r.page_restored==(i<6));
  f=(struct fake){.busy_at=-1,.fail_poll=i};spd_reader_init(&r,transport(&f),0,1);run(&r);
  assert(r.result==SPD_IO_ERROR);assert(r.page_restored==(i<6));
 }
 f=(struct fake){.busy_at=-1,.mismatch=1};spd_reader_init(&r,transport(&f),0,1);run(&r);
 assert(r.result==SPD_MISMATCH && r.page_restored);
 f=(struct fake){.busy_at=-1,.pending=1};spd_reader_init(&r,transport(&f),0,1);run(&r);
 assert(r.result==SPD_DEADLINE && !r.page_restored && f.starts==2);
 f=(struct fake){.busy_at=-1};spd_reader_init(&r,transport(&f),0,1);spd_reader_tick(&r,100000);run(&r);
 assert(r.result==SPD_DEADLINE && r.page_restored);
 f=(struct fake){.busy_at=1,.fail_poll=1};spd_reader_init(&r,transport(&f),0,1);run(&r);
 assert(r.result==SPD_IO_ERROR && !r.page_restored && f.starts==1);
 puts("SPD reader model controls PASS; no AMD adapter or hardware qualification");
}
