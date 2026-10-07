#include <stdint.h>
#include <stddef.h>
#include "rtio_csr.h"
extern void worker_trap(void);
void worker_uart(const uint8_t *s,size_t n) {
 volatile uint32_t *uart=(void *)0xFF000000;
 for(size_t i=0;i<n;i++) {while(uart[0x2c/4]&(1u<<4)) {} uart[0x30/4]=s[i];}
 uart[0x30/4]='\n';
}
int64_t worker_counter(void) {
 *(volatile uint32_t *)RTIO_COUNTER_UPDATE=1;
 asm volatile("dsb sy" ::: "memory");
 uint32_t hi=*(volatile uint32_t *)RTIO_COUNTER;
 uint32_t lo=*(volatile uint32_t *)(RTIO_COUNTER+4);
 return ((uint64_t)hi<<32)|lo;
}
void worker_rtio_init(void) {
 *(volatile uint32_t *)RTIO_CORE_RESET=1;
 *(volatile uint32_t *)RTIO_CORE_RESET_PHY=1;
 asm volatile("dsb sy" ::: "memory");
}
void *memcpy(void *dst, const void *src, size_t n) {
    uint8_t *d = dst; const uint8_t *s = src; while (n--) *d++ = *s++; return dst;
}
void *memset(void *dst, int c, size_t n) {
    uint8_t *d = dst; while (n--) *d++ = c; return dst;
}
void *memmove(void *dst, const void *src, size_t n) {
    uint8_t *d = dst; const uint8_t *s = src;
    if ((uintptr_t)d < (uintptr_t)s) return memcpy(dst, src, n);
    while (n) { n--; d[n] = s[n]; } return dst;
}
int memcmp(const void *a, const void *b, size_t n) {
    const uint8_t *x = a, *y = b;
    while (n--) { if (*x != *y) return *x - *y; x++; y++; } return 0;
}
int bcmp(const void *a,const void *b,size_t n) {return memcmp(a,b,n);}
void __aeabi_unwind_cpp_pr0(void) {worker_trap();}
void __aeabi_unwind_cpp_pr1(void) {worker_trap();}
void _Unwind_Resume(void *exception) {(void)exception;worker_trap();}
