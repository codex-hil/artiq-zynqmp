// SPDX-License-Identifier: LGPL-3.0-or-later
// OCM model only; no physical DDR backend. No cache/MMU control changes.
.section .text.vectors,"ax"
.global __vectors
__vectors:
.set slot,0
.rept 16
 mov x14,#slot
 b model_exception
 .space 120,0
 .set slot,slot+1
.endr
.section .text.entry,"ax"
.global _start,__ocm_start,model_done,model_rejected,model_fault_done
_start:
__ocm_start:
 mrs x0,CurrentEL
 cmp x0,#12
 b.ne model_rejected
 adr x1,__vectors
 msr VBAR_EL3,x1
 isb
 mrs x2,VBAR_EL3
 cmp x1,x2
 b.ne model_rejected
 // Refuse active translation/cache at all levels; no attempt to disable them.
 mov x3,#0x1005
 mrs x1,SCTLR_EL3
 tst x1,x3
 b.ne model_rejected
 mrs x1,SCTLR_EL2
 tst x1,x3
 b.ne model_rejected
 mrs x1,SCTLR_EL1
 tst x1,x3
 b.ne model_rejected
 mrs x1,DAIF
 mov x3,#0x2c0
 and x1,x1,x3
 cmp x1,#0x2c0
 b.ne model_rejected
 ldr x1,=__stack0_end
 mov sp,x1
 ldr x1,=__bss_start
 ldr x2,=__bss_end
1:
 cmp x1,x2
 b.hs 2f
 str xzr,[x1],#8
 b 1b
2:
 bl ocm_model_main
 cbnz x0,model_rejected
 mov x15,#0x33
model_done:
 b model_done
model_rejected:
 mov x15,#0xee
3: b 3b
model_exception:
 mrs x16,CurrentEL
 mrs x17,ESR_EL3
 mrs x18,FAR_EL3
 mrs x19,ELR_EL3
 mrs x20,SPSR_EL3
 mrs x21,DAIF
 mov x15,#0xf3
model_fault_done:
 b model_fault_done
