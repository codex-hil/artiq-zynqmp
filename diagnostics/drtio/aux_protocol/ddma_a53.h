/* AMD standalone A53 binding, inactive until service wiring; LGPL-3.0-or-later. */
#pragma once
#include <string.h>
#include "xil_cache.h"
#include "sleep.h"
#include "ddma_backend.h"
static inline uint32_t ddma_a53_read(void *context,uintptr_t address) {
 (void)context;__asm__ volatile("dsb sy":::"memory");
 return *(volatile uint32_t *)address;
}
static inline void ddma_a53_write(void *context,uintptr_t address,uint32_t value) {
 (void)context;*(volatile uint32_t *)address=value;
 __asm__ volatile("dsb sy":::"memory");
}
static inline int ddma_a53_copy(void *context,uintptr_t address,const uint8_t *data,size_t length) {
 (void)context;
 if(address!=DDMA_ARENA || length!=2048)return -1;
 memcpy((void *)address,data,length);return 0;
}
static inline void ddma_a53_flush(void *context,uintptr_t address,size_t length) {
 (void)context;Xil_DCacheFlushRange(address,length);
 __asm__ volatile("dsb sy":::"memory");
}
static inline void ddma_a53_delay(void *context) {(void)context;usleep(1000);}
/* time/ready are mandatory live board-specific callbacks. No fabricated TSC. */
static inline struct ddma_backend ddma_a53_bind(void *context,
 int (*time)(void *,uint64_t *),int (*ready)(void *)) {
 struct ddma_backend b={context,ddma_a53_read,ddma_a53_write,ddma_a53_copy,
  ddma_a53_flush,time,ready,ddma_a53_delay,0};return b;
}
