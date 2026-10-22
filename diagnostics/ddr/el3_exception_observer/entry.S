// SPDX-License-Identifier: LGPL-3.0-or-later
// Debugger must install/read back VBAR_EL3 while CPU0 is halted, BEFORE con.
// No DAIF changes, data accesses, stack, cache operations or DDR writes.
.section .text.vectors,"ax"
.global observer_vectors
observer_vectors:
.set vector_slot, 0
.rept 16
    mov x14, #vector_slot
    b observer_exception
    .space 120, 0
    .set vector_slot, vector_slot + 1
.endr

.section .text.entry,"ax"
.global _start, observer_done, observer_wrong_el, observer_exception
.global observer_fault_probe, observer_fault_done
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
observer_done:
    b observer_done
observer_wrong_el:
    mov x15, #0xee
1:
    b 1b

// Separate deliberate synchronous exception entry for later bounded validation.
// Normal entry never reaches it. No loader is provided in this checkpoint.
observer_fault_probe:
    mrs x0, CurrentEL
    cmp x0, #12
    b.ne observer_wrong_el
    brk #0x53
    b observer_wrong_el

observer_exception:
    mrs x16, CurrentEL
    cmp x16, #12
    b.ne observer_wrong_el
    mrs x17, ESR_EL3
    mrs x18, FAR_EL3
    mrs x19, ELR_EL3
    mrs x20, SPSR_EL3
    mrs x21, DAIF
    mov x15, #0xf3
observer_fault_done:
    b observer_fault_done
