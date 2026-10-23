/* SPDX-License-Identifier: LGPL-3.0-or-later */
ENTRY(_start)
PHDRS { text PT_LOAD FLAGS(5); data PT_LOAD FLAGS(6); }
SECTIONS {
 . = 0xfffc8000;
 .text : { KEEP(*(.text.vectors)) KEEP(*(.text.entry)) *(.text*) } :text
 .rodata : { *(.rodata*) } :text
 . = ALIGN(16);
 .data : { *(.data*) } :data
 .bss (NOLOAD) : {
  __bss_start = .;
  *(.bss*) *(COMMON)
  . = ALIGN(16);
  __bss_end = .;
 } :data
 . = 0xfffe0000;
 .stack (NOLOAD) : { __stack0_start = .; . += 0x4000; __stack0_end = .; } :data
 /DISCARD/ : { *(.comment*) *(.note*) *(.eh_frame*) }
}
ASSERT(__vectors == 0xfffc8000, "Vector moved")
ASSERT(_start == 0xfffc8800, "Entry moved")
ASSERT(__bss_end < 0xfffd0000, "Code/data exceed lower OCM allocation")
ASSERT(__stack0_end <= 0x100000000, "Stack outside OCM")
