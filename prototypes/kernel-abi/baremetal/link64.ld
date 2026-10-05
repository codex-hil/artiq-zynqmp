ENTRY(_start)
SECTIONS {
    . = 0x40100000;
    .text : { KEEP(*(.text.start)) *(.text*) }
    /DISCARD/ : { *(.comment) *(.note*) }
}
