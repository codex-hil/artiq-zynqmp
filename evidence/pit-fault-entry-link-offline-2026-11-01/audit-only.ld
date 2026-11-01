/* SPDX-License-Identifier: LGPL-3.0-or-later */
/* Synthetic non-PMU addresses: static relocation fixture, never deploy. */
OUTPUT_ARCH(microblaze)
ENTRY(pit_fault_sw_entry_audit)
MEMORY { CODE (rx) : ORIGIN = 0x10000, LENGTH = 0x100
         SLOT (rw) : ORIGIN = 0x20000, LENGTH = 0x40 }
PHDRS { code PT_LOAD FLAGS(5); slot PT_LOAD FLAGS(6); }
SECTIONS {
 .text : { KEEP(*(.text.pit_fault_sw_entry_audit)) KEEP(*(.text.pit_fault_hw_entry_audit)) } > CODE :code
 .forbidden : { *(.vectors*) *(.stack*) *(.heap*) } > CODE :code
 .bss (NOLOAD) : { KEEP(*(.bss.pit_fault_entry_slot)) } > SLOT :slot
 /DISCARD/ : { *(.comment) *(.note*) }
 ASSERT(SIZEOF(.text) == 0x100, "exact two-entry code size required")
 ASSERT(SIZEOF(.bss) == 0x40, "exact private slot required")
 ASSERT(SIZEOF(.forbidden) == 0, "vectors/stack/heap forbidden")
 ASSERT(pit_fault_entry_slot == 0x20000, "slot address changed")
}
