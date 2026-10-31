/* SPDX-License-Identifier: LGPL-3.0-or-later */
#if !defined(__MICROBLAZE__) || !defined(ARTIQ_PIT_FAULT_ENTRY_AUDIT_ONLY)
#error "Explicit MicroBlaze assembly-entry audit opt-in required; no deployment"
#endif
/* Standalone, unreferenced candidate. NOT bound to vectors or runtime.
 * Supplied platform assumptions: special-register access and dedicated slot
 * memory valid; no nested entry. No stack/arguments/calls/return. No EDR read.
 * A committed receipt is not sleep, visibility, recovery or session proof. */
.section .bss.pit_fault_entry_slot,"aw",@nobits
.balign 8
.globl pit_fault_entry_slot
.type pit_fault_entry_slot,@object
pit_fault_entry_slot:
.skip 64
.size pit_fault_entry_slot,64

.macro FAULT_ENTRY name,route
.section .text.\name,"ax",@progbits
.balign 4
.globl \name
.type \name,@function
\name:
 mfs r3,rmsr
 mfs r4,resr
 mfs r5,rear
 addik r8,r0,pit_fault_entry_slot
 swi r0,r8,0
 mbar 1
 addik r9,r0,0x50465831
 swi r9,r8,4
 addik r9,r0,1
 swi r9,r8,8
 addik r9,r0,\route
 swi r9,r8,12
 addik r9,r0,7
 swi r9,r8,16
 swi r3,r8,20
 swi r4,r8,24
 swi r5,r8,28
 swi r0,r8,32
 swi r0,r8,36
 swi r0,r8,40
 swi r0,r8,44
 swi r0,r8,48
 swi r0,r8,52
 swi r0,r8,56
 swi r0,r8,60
 mbar 1
 addik r9,r0,1
 swi r9,r8,0
.Lstop_\name:
 bri .Lstop_\name
 nop
.size \name,.-\name
.endm
FAULT_ENTRY pit_fault_sw_entry_audit,1
FAULT_ENTRY pit_fault_hw_entry_audit,2
