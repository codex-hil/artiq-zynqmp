/* SPDX-License-Identifier: LGPL-3.0-or-later */
#if !defined(__MICROBLAZE__) || !defined(ARTIQ_PIT_TERMINAL_AUDIT_ONLY)
#error "MicroBlaze audit-only compilation required; no deployment profile"
#endif
/* Standalone static-flow probe, no runtime hook or MMIO/backend. Interrupt
 * policy, capture, visibility and recovery must be qualified separately.
 * Wake resumes at the branch and re-enters sleep; no C return is reachable.
 */
__attribute__((noinline,noreturn,used)) void pit_terminal_audit(void)
{
    __asm__ __volatile__("mbar 1\n1: sleep\nbri 1b\n" ::: "memory");
    __builtin_unreachable();
}
