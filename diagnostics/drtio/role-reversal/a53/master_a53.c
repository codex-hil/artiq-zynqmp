/* LGPL-3.0-or-later. Compile-only A53 MMIO binding; no entry or live execution. */
#include "master_driver.h"
#if !defined(__aarch64__)
#error "AArch64 target required for this direct MMIO binding"
#endif
static int gm_a53_read(void *p,uint32_t a,uint32_t *v) {
 (void)p;if((a&3)||a<0xa0000000u||a>=0xa0002000u||!v)return -1;
 *v=*(volatile uint32_t *)(uintptr_t)a;
 __asm__ volatile("dsb sy" ::: "memory");return 0;
}
static int gm_a53_write(void *p,uint32_t a,uint32_t v) {
 (void)p;if((a&3)||a<0xa0000000u||a>=0xa0002000u)return -1;
 *(volatile uint32_t *)(uintptr_t)a=v;return 0;
}
static int gm_a53_fence(void *p) {(void)p;__asm__ volatile("dsb sy" ::: "memory");return 0;}
struct gm_bus gm_a53_bus(void) {
 struct gm_bus b={0,gm_a53_read,gm_a53_write,gm_a53_fence};return b;
}
/* Retain the exact scheduler in compile-only object for instruction inspection. */
struct gm_result gm_a53_compile_schedule(uint32_t d,uint16_t ch,uint64_t ts,uint32_t v) {
 struct gm_bus b=gm_a53_bus();return gm_schedule(&b,d,ch,ts,v,64);
}
