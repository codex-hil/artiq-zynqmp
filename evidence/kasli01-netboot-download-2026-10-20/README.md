# KASLI01 physical network boot/download

PASS under the shared KASLI01 lease, held through diagnostic restoration.
JTAG DNA matched 0x007865085f704854 before SRAM programming. The new
bootloader passed CRC, SDRAM initialization and its inherited memory test.
Three IPv6 TCP connections confirmed unknown-command rejection, refusal to
boot without a payload and listener recovery; neighbor MAC matched KASLI01.
The bootloader acknowledged receipt of 1756420 bytes of runtime in RAM.
No boot command was sent; runtime execution and RAM readback were NOT_RUN.
This is an initial SDRAM test, not a long-duration DDR qualification.

Full-checker diagnostic was restored and identity/EEM/GTP/SFP-disable registers
checked. No flash/OTP or Si5324 profile writes, no Genesys or other Kasli
access. The wrapper released the board lock on completion.

`argv.json` records the exact command. The FPGA build qualification is in
`../kasli01-master-fpga-2026-10-20`. Next run the already guarded runtime
execution/management test with the KASLI01-specific validated clock baseline
and restore plan, then qualify external DRTIO with Genesys separately.
