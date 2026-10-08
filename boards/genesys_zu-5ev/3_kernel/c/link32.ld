ENTRY(_start)
SECTIONS {
    . = 0x20200000;
    .text : { __text_start = .; KEEP(*(.text.start)) *(.text*) __text_end = .; }
    .rodata : { *(.rodata*) }
    .ARM.extab : { *(.ARM.extab*) }
    .ARM.exidx : { __exidx_start = .; *(.ARM.exidx*) __exidx_end = .; }
    .data : { *(.data*) }
    . = ALIGN(4096);
    _bss_start = .;
    .bss (NOLOAD) : { *(.bss*) *(COMMON) }
    . = ALIGN(4); _bss_end = .;
    . = ALIGN(16); . += 65536; _stack_top = .;
    ASSERT(_stack_top < 0x20400000, "CPU1 image exceeds reserved memory")
    /DISCARD/ : { *(.comment) *(.note*) }
}
