INCLUDE memory.x
SECTIONS {
 .text : ALIGN(0x1000) { KEEP(*(.vectors)) *(.boot_ocm) *(.text .text.*) } > CODE
 .rodata : ALIGN(0x1000) { *(.rodata .rodata.*) } > CODE
 .data : ALIGN(8) { __data_start = .; *(.data .data.*) . = ALIGN(8); __data_end = .; } > DATA
 __data_load_start = LOADADDR(.data);
 .bss (NOLOAD) : ALIGN(8) { __bss_start = .; *(.bss .bss.*) *(COMMON) . = ALIGN(8); __bss_end = .; } > DATA
 .stack (NOLOAD) : ALIGN(0x1000) { . += 0x4000; __stack0_end = .; __stack1_end = .; __stack2_end = .; __stack3_end = .; } > DATA
 /DISCARD/ : { *(.note .note*) *(.boot) }
}
PROVIDE(_sync_handler = __default_handler);
PROVIDE(_irq_handler = __default_handler);
PROVIDE(_fiq_handler = __default_handler);
PROVIDE(_serror_handler = __default_handler);
PROVIDE(_exit_handler = __default_exit_handler);
ENTRY(__ocm_start)

__start = __ocm_start;
