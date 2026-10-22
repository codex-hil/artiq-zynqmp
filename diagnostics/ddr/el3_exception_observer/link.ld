/* SPDX-License-Identifier: LGPL-3.0-or-later */
ENTRY(_start)
PHDRS { text PT_LOAD FLAGS(5); }
SECTIONS {
 . = 0xfffc8000;
 .text : { KEEP(*(.text.vectors)) KEEP(*(.text.entry)) } :text
 /DISCARD/ : { *(.note*) *(.comment*) }
}
ASSERT(observer_vectors == 0xfffc8000, "Unexpected vector address")
ASSERT(_start == 0xfffc8800, "Unexpected entry address")
ASSERT(SIZEOF(.text) < 0x1000, "Observer grew beyond reviewed OCM page")
