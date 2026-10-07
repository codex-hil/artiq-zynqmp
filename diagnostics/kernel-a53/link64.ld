ENTRY(_start)
SECTIONS {
 . = 0x20000000;
 .text : { KEEP(*(.text.start)) *(.text*) }
 /DISCARD/ : { *(.comment) *(.note*) }
}
