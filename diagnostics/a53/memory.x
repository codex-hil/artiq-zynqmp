/* Exclusive bare-metal A53 application after Piotr/AMD FSBL initialized DDR.
 * This range must not be used while Linux/OpenAMP is running.
 */
MEMORY {
    DDR (rwx) : ORIGIN = 0x00100000, LENGTH = 16M
}
REGION_ALIAS("CODE", DDR)
REGION_ALIAS("DATA", DDR)
__stack_size = 64K;
ENTRY(__start)
