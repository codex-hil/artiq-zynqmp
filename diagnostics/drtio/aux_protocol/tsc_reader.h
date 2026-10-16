/* Ordered snapshot reader with conservative age bound; LGPL-3.0-or-later.
 * Single firmware owner; callbacks must provide ordered MMIO and monotonic ns.
 * Target fine3 TSC rate must be <=2 mu/ns; this is not phase calibration.
 */
#pragma once
#include <stdint.h>
#include <stddef.h>
#define TS_LOAD ((uintptr_t)0xa0001820)
#define TS_REQUEST ((uintptr_t)0xa0001840)
#define TS_BUSY ((uintptr_t)0xa0001844)
#define TS_VALID ((uintptr_t)0xa0001848)
#define TS_VALUE ((uintptr_t)0xa000184c)
struct tsc_reader {
 void *context;
 uint32_t (*read)(void *,uintptr_t);
 void (*write)(void *,uintptr_t,uint32_t);
 int (*monotonic_ns)(void *,uint64_t *);
 int (*ready)(void *);
 void (*delay)(void *);
};
/* Returns an upper estimate of current fine3 TSC, never the stale sample alone.
 * Total elapsed since before request bounds sample age; 2x covers target rate.
 * Failure leaves caller output unchanged. No host/wall-time substitution.
 */
static inline int tsc_read_upper(void *context,uint64_t *value) {
 struct tsc_reader *r=context;uint64_t begin,end,sample;uint32_t epoch;
 if(!r || !value || !r->read || !r->write || !r->monotonic_ns || !r->ready || !r->delay)return -1;
 if(!r->ready(r->context) || r->monotonic_ns(r->context,&begin))return -1;
 epoch=r->read(r->context,TS_LOAD);
 if(!epoch || r->read(r->context,TS_BUSY))return -1;
 r->write(r->context,TS_REQUEST,1); /* ordered completion before subsequent reads */
 for(unsigned i=0;i<100;i++) {
  if(!r->read(r->context,TS_BUSY) && r->read(r->context,TS_VALID)) {
   sample=(uint64_t)r->read(r->context,TS_VALUE)<<32;
   sample|=r->read(r->context,TS_VALUE+4);
   if(!r->ready(r->context) || r->read(r->context,TS_LOAD)!=epoch ||
      r->monotonic_ns(r->context,&end) || end<begin || end-begin>100000)return -1;
   uint64_t allowance=2*(end-begin)+1000;
   if(sample>INT64_MAX || allowance>INT64_MAX-sample)return -1;
   *value=sample+allowance;return 0;
  }
  r->delay(r->context);
 }
 return -1;
}
