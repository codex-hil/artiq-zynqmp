.syntax unified
.arm
.section .text.start,"ax"
.global _start
_start:
    ldr sp, =_stack_top
    ldr r0, =vectors
    mcr p15, 0, r0, c12, c0, 0
    isb
    /* EL1/SVC AArch32: enable CP10/CP11 and VFP/NEON. */
    mrc p15, 0, r0, c1, c0, 2
    orr r0, r0, #(15 << 20)
    mcr p15, 0, r0, c1, c0, 2
    isb
    mov r0, #(1 << 30)
    vmsr fpexc, r0
    ldr r0, =_bss_start
    ldr r1, =_bss_end
    mov r2, #0
1:  cmp r0, r1
    strlo r2, [r0], #4
    blo 1b
    bl probe_main
2:  wfe
    b 2b

.balign 32
vectors:
    b _start
    b trapped
    b trapped
    b trapped
    b trapped
    b trapped
    b trapped
    b trapped
trapped:
#ifdef GENESYS_HARDWARE
    ldr r0, =0x200ff004
    str lr, [r0]
    mrs r1, spsr
    str r1, [r0, #4]
#endif
    ldr sp, =_stack_top
    b probe_fail
.section .note.GNU-stack,"",%progbits
