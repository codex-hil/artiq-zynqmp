.section .text.start,"ax"
.global _start
_start:
    /* JTAG diagnostic on CPU1, reset EL3/AArch64; no shared peripheral setup. */
    mrs x0, CurrentEL
    cmp x0, #12
    b.ne failed
    msr cptr_el3, xzr
    msr cptr_el2, xzr
    mov x0, #0x501
    msr scr_el3, x0
    msr hcr_el2, xzr
    /* Explicit cache/MMU-off policy for this diagnostic only. */
    mrs x0, sctlr_el1
    bic x0, x0, #1
    bic x0, x0, #4
    bic x0, x0, #0x1000
    bic x0, x0, #0x2000
    msr sctlr_el1, x0
    mov x0, #0x1d3
    msr spsr_el3, x0
    mov x0, #0x20200000
    msr elr_el3, x0
    isb
    eret
failed:
    wfe
    b failed
