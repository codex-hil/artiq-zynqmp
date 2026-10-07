ENTRY(_start)
SECTIONS {
    . = 0x20200000;
    .text : { KEEP(*(.text.start)) *(.text*) }
    .rodata : { *(.rodata*) }
    .ARM.exidx : { *(.ARM.exidx*) }
    .data : { *(.data*) }
    . = ALIGN(4096);
    _bss_start = .;
    .bss (NOLOAD) : { *(.bss*) *(COMMON) }
    . = ALIGN(4); _bss_end = .;
    . = ALIGN(16); . += 65536; _stack_top = .;
    /DISCARD/ : { *(.comment) *(.note*) }
}
