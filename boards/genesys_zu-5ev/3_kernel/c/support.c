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
/* CSR sequencing follows M-Labs rtio_csr.rs. Addresses/word counts are
 * generated from this bitstream; 64-bit MiSoC words are MSW first. */
static uint32_t read32(uintptr_t a) { return *(volatile uint32_t *)a; }
static void write32(uintptr_t a, uint32_t v) {
 *(volatile uint32_t *)a=v; asm volatile("dsb sy" ::: "memory");
}
static uint64_t read64(uintptr_t a) {
 uint32_t hi=read32(a), lo=read32(a+4); return ((uint64_t)hi<<32)|lo;
}
static void write64(uintptr_t a,uint64_t v) {write32(a,v>>32);write32(a+4,v);}
int64_t worker_now(void) {return read64(RTIO_NOW);}
void worker_at(int64_t t) {write64(RTIO_NOW,(uint64_t)t);}
uint32_t worker_output(int32_t target,int32_t data) {
 write32(RTIO_TARGET,(uint32_t)target);
 write32(RTIO_O_DATA+4*(RTIO_O_DATA_WORDS-1),(uint32_t)data);
 uint32_t status=read32(RTIO_O_STATUS);
 /* WAIT is backpressure, not permission to send a duplicate event. */
 if(status&1) {
  int64_t deadline=worker_counter()+125000000; /* bounded initial bring-up */
  while(read32(RTIO_O_STATUS)&1) {if(worker_counter()>deadline)return 8;}
 }
 return status&6;
}
uint32_t worker_input(int64_t timeout,int32_t channel) {
 write32(RTIO_TARGET,(uint32_t)channel<<8);
 write64(RTIO_I_TIMEOUT,(uint64_t)timeout);
 uint32_t status;
 int64_t deadline=worker_counter()+125000000;
 if(timeout>deadline && timeout<INT64_MAX-125000000)deadline=timeout+125000000;
 do {status=read32(RTIO_I_STATUS);if(worker_counter()>deadline)return 16;}
 while(status&4);
 return status;
}
int64_t worker_input_timestamp(void) {return read64(RTIO_I_TIMESTAMP);}
int32_t worker_input_data(void) {return read32(RTIO_I_DATA+4*(RTIO_I_DATA_WORDS-1));}
uint32_t worker_async_errors(void) {
 uint32_t e=read32(RTIO_CORE_ASYNC_ERROR)&7;
 if(e)write32(RTIO_CORE_ASYNC_ERROR,e); /* write-one-to-clear */
 return e;
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
