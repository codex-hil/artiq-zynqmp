/* Exclusive JTAG diagnostic: no DDR access, only 256 KiB PS OCM. */
MEMORY { OCM (rwx) : ORIGIN = 0xFFFC0000, LENGTH = 256K }
REGION_ALIAS("CODE", OCM)
REGION_ALIAS("DATA", OCM)
__stack_size = 64K;
