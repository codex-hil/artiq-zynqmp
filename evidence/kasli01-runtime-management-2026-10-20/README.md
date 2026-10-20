# KASLI01 runtime, management and counter/RPC

Physical PASS. The guarded wrapper held KASLI01 and Genesys leases in sorted
order throughout loading, testing and restoration. Genesys was not accessed;
Kasli03/04 were not leased or accessed. JTAG DNA matched KASLI01 before SRAM
programming. Netboot downloaded the per-board runtime; the expected first
clock-switch reboot required a second RAM download/boot. Runtime then started.

Two independent standard `artiq_coremgmt log` connections passed. Two standard
`artiq_run` counter/RPC experiments passed, with counter advances of 1124648
and 1124712 machine units. No TTL writes were made. This does not qualify
the external DRTIO link, remote DIO, DMA or deterministic latency on KASLI01.

Diagnostic SRAM/register restoration and volatile Si5324 profile restoration
passed. Readback and approximate host-referenced frequency checks passed;
these are not jitter or precision-frequency measurements. The intentional
soft-reset value-byte NACK is permitted by the reviewed clock restore plan.
All other restore writes acknowledged, with no retry. Flash/OTP untouched.
Both leases released by the completed wrapper.

See `argv.json` for the command and `results.json` for detailed assertions.
Next prepare a KASLI01-specific external Genesys qualification configuration
and validate the physical DRTIO path before delayed-DMA fault tests.
