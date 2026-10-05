.section .text.start,"ax"
.global _start
_start:
    /* QEMU virt enters EL3/AArch64. Only CPU0 is used. */
    mrs x0, CurrentEL
    cmp x0, #12
    b.ne failed
    msr cptr_el3, xzr
    msr cptr_el2, xzr
    /* EL2 remains AArch64; HCR.RW=0 selects AArch32 at EL1. */
    mov x0, #0x501             // SCR: NS, HCE, RW
    msr scr_el3, x0
    msr hcr_el2, xzr
    mov x0, #0x1d3             // AArch32 SVC, A/I/F masked
    msr spsr_el3, x0
    mov x0, #0x40200000
    msr elr_el3, x0
    isb
    eret
failed:
    wfe
    b failed
