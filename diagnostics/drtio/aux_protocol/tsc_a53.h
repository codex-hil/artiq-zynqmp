/* A53 architectural timer for snapshot age only; LGPL-3.0-or-later. */
#pragma once
#include "ddma_a53.h"
#include "tsc_reader.h"
static inline int tsc_a53_monotonic_ns(void *context,uint64_t *value) {
 uint64_t ticks,frequency;(void)context;
 __asm__ volatile("isb; mrs %0, cntpct_el0":"=r"(ticks)::"memory");
 __asm__ volatile("mrs %0, cntfrq_el0":"=r"(frequency));
 if(!frequency)return -1;
 /* Round upwards to retain a conservative elapsed-time allowance. */
 __uint128_t ns=((__uint128_t)ticks*1000000000+frequency-1)/frequency;
 if(ns>UINT64_MAX)return -1;
 *value=(uint64_t)ns;return 0;
}
static inline void tsc_a53_delay(void *context) {(void)context;usleep(1);}
static inline struct tsc_reader tsc_a53_bind(void *context,int (*ready)(void *)) {
 struct tsc_reader r={context,ddma_a53_read,ddma_a53_write,
  tsc_a53_monotonic_ns,ready,tsc_a53_delay};return r;
}
