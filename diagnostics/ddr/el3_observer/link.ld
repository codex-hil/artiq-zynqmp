/* SPDX-License-Identifier: LGPL-3.0-or-later */
ENTRY(_start)
SECTIONS {
  . = 0xfffc0000;
  .text : { KEEP(*(.text.entry)) }
  /DISCARD/ : { *(.note*) *(.comment*) }
}
