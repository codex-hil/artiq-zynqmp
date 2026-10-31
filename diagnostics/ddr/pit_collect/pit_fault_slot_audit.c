/* SPDX-License-Identifier: LGPL-3.0-or-later */
#if !defined(__MICROBLAZE__) || !defined(ARTIQ_PIT_FAULT_SLOT_AUDIT_ONLY)
#error "Explicit MicroBlaze fault-slot audit opt-in required; no deployment"
#endif
#include "pit_fault_slot_audit.h"
#include "pit_fault_record.h"
volatile uint32_t pit_fault_slot_audit[16] __attribute__((used,aligned(8),section(".bss.pit_fault_slot_audit")));
static volatile uint32_t fault_slot_consumed;
__attribute__((noinline,used)) int pit_fault_store_audit(uint32_t route,uint32_t valid,const uint32_t registers[4])
{
 uint32_t staged[16];
 unsigned i;
 if(fault_slot_consumed||!registers||((uintptr_t)registers&3u))return -1;
 for(i=0;i<16;i++)if(pit_fault_slot_audit[i])return -1;
 /* This flag is one-context bookkeeping, not atomic NMI/exception exclusion. */
 fault_slot_consumed=1;
 for(i=0;i<16;i++)((volatile uint32_t *)staged)[i]=0;
 if(pit_fault_format(staged,route,valid,registers))return -1;
 pit_fault_slot_audit[0]=0;
 __asm__ volatile("mbar 1" ::: "memory");
 for(i=1;i<16;i++)pit_fault_slot_audit[i]=staged[i];
 __asm__ volatile("mbar 1" ::: "memory");
 pit_fault_slot_audit[0]=1;
 return 0; /* Returned stores, not external visibility or exception recovery. */
}
