// SPDX-License-Identifier: LGPL-3.0-or-later
// Register-only observer: no stack, memory, UART, cache or control writes.
.section .text.entry,"ax"
.global _start, observer_el3_done, observer_wrong_el
.type _start, %function
_start:
    mrs x0, CurrentEL
    cmp x0, #12
    b.ne observer_wrong_el
    mrs x1, SCTLR_EL3
    mrs x2, SCR_EL3
    mrs x3, SCTLR_EL2
    mrs x4, SCTLR_EL1
    mrs x5, HCR_EL2
    mrs x6, DAIF
    mrs x7, MPIDR_EL1
    mov x8, sp
    adr x9, _start
    mov x15, #0x33
observer_el3_done:
    b observer_el3_done
observer_wrong_el:
    mov x15, #0xee
1:
    b 1b
.size _start, . - _start
