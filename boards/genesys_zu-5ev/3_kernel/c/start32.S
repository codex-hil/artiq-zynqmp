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
    bl worker_main
    /* An uncaught kernel exception discards only CPU1's current Rust stack.
       CPU0/networking remains active; heaps are rebuilt before accepting LOAD. */
.global worker_recover
worker_recover:
    ldr sp, =_stack_top
    b worker_main
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

    ldr r0, =0x200ff080
    str lr, [r0]
    mrs r1, spsr
    str r1, [r0, #4]

    ldr sp, =_stack_top
    b worker_trap
.section .note.GNU-stack,"",%progbits

.section .text.worker_invoke,"ax"
.global worker_invoke
.type worker_invoke,%function
worker_invoke:
    .fnstart
    push {r4, lr}
    .save {r4, lr}
    blx r0
.global worker_unwind_boundary
worker_unwind_boundary:
    pop {r4, pc}
    .fnend
.size worker_invoke, .-worker_invoke
