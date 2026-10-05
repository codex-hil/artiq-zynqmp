#include <stdint.h>
#include <stddef.h>

/* QEMU virt PL011; deliberately not a Genesys UART driver. */
static void puts_uart(const char *s) {
    volatile uint32_t *uart = (void *)0x09000000;
    while (*s) { while (uart[6] & (1u << 5)) {} uart[0] = *s++; }
}
static void quit(int code) {
    uint32_t block[2] = {0x20026, (uint32_t)code};
    register uint32_t r0 asm("r0") = 0x20; // SYS_EXIT_EXTENDED
    register void *r1 asm("r1") = block;
    asm volatile("svc 0x123456" : "+r"(r0) : "r"(r1) : "memory");
    for (;;) {}
}
void probe_fail(void) { puts_uart("FAIL: bare-metal kernel ABI probe\n"); quit(3); }
static int64_t now;
static unsigned init_calls, integer_calls, float_calls, output_calls, writebacks;
static void rtio_init(void) { init_calls++; }
static int64_t rtio_get_counter(void) { return 0; }
static void at_mu(int64_t t) { now = t; }
static int64_t now_mu(void) { return now; }
static void delay_mu(int64_t dt) { now += dt; }
static void abi_check64(int64_t v) {
    if (v != (integer_calls == 0 ? INT64_C(0x1234567887654321) : INT64_C(0x100000052))) probe_fail();
    integer_calls++;
}
static double abi_check_float(double v) {
    if (v != (float_calls == 0 ? 1.25 : 3.75)) probe_fail();
    float_calls++;
    return v + 2.5;
}
static void rtio_output(int32_t target, int32_t data) {
    if (target != 0 || data != (output_calls == 0 ? 1 : 0) ||
        now != (output_calls == 0 ? INT64_C(0x100000020) : INT64_C(0x100000052))) probe_fail();
    output_calls++;
}
struct cslice { const uint8_t *ptr; size_t len; };
static void rpc_send_async(uint32_t service, const struct cslice *tag, const void *const *data) {
    (void)data;
    if (service != 0 || tag->len != 2 || tag->ptr[0] != ':' || tag->ptr[1] != 'n') probe_fail();
    writebacks++;
}
static int name_eq(const uint8_t *name, size_t size, const char *expected) {
    size_t i = 0;
    while (expected[i]) { if (i == size || name[i] != expected[i]) return 0; i++; }
    return i == size;
}
uint32_t resolve_name(const uint8_t *name, size_t size) {
#define SYM(s) if (name_eq(name, size, #s)) return (uint32_t)(uintptr_t)s;
    SYM(rtio_init) SYM(rtio_get_counter) SYM(at_mu) SYM(now_mu) SYM(delay_mu)
    SYM(abi_check64) SYM(abi_check_float) SYM(rtio_output) SYM(rpc_send_async)
    if (name_eq(name, size, "__nac3_resume") || name_eq(name, size, "__nac3_personality"))
        return (uint32_t)(uintptr_t)probe_fail;
    return 0;
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
void rust_eh_personality(void) { probe_fail(); }
void __aeabi_unwind_cpp_pr0(void) { probe_fail(); }
void __aeabi_unwind_cpp_pr1(void) { probe_fail(); }
int bcmp(const void *a, const void *b, size_t n) { return memcmp(a, b, n); }
extern void execute_kernel(void);
void probe_main(void) {
    uint32_t cpsr, midr, sctlr;
    asm volatile("mrs %0, cpsr" : "=r"(cpsr));
    asm volatile("mrc p15, 0, %0, c0, c0, 0" : "=r"(midr));
    asm volatile("mrc p15, 0, %0, c1, c0, 0" : "=r"(sctlr));
    if ((cpsr & 0x1f) != 0x13 || ((midr >> 4) & 0xfff) != 0xd03) probe_fail();
    if (sctlr & ((1u << 12) | (1u << 2) | 1u)) probe_fail(); // caches/MMU disabled
    asm volatile("veor q8, q8, q8" ::: "d16", "d17"); // actual NEON instruction
    puts_uart("A53 EL1/AArch32: startup and VFP enabled\n");
    execute_kernel();
    if (init_calls != 1 || integer_calls != 2 || float_calls != 2 || output_calls != 2 || writebacks != 1) probe_fail();
    puts_uart("PASS: A53 bare-metal NAC3 kernel; upstream loader; i64/hard-float/timeline ABI\n");
    quit(0);
}
