# KASLI01 external DRTIO attempt: startup failed, baselines restored

The bounded parent held KASLI01 and Genesys locks throughout programming,
UART/network tests and restoration. Exact KASLI01 DNA matched. Standard
master netboot, runtime, management and counter/RPC passed again.

External satellite firmware printed `AUX_EXTERNAL START upstream-codec
split-reset RTIO-backend`, then `TEST ARTIQ_AUX_FIRMWARE FAIL`. No cold-release
PASS, TSC ACK or DIO test was reached. Therefore external DRTIO is NOT
QUALIFIED. The current firmware emits the same generic FAIL for magic,
reset-release and RX-up checks; this log cannot distinguish those causes.
A disconnected/wrong optical path is possible but is not proved by this log.
Do not reuse historical KASLI03 hardware success as KASLI01 proof.

KASLI01 diagnostic/register and volatile Si5324 restoration PASS; Genesys
normal local runtime/debug/Ethernet restoration PASS at 192.168.2.3. Both
leases released. Flash/OTP/SD and Genesys Si configuration untouched.
Kasli03/04 and their running Vivado build untouched.

The historical JTAG server was absent. A Genesys-only filtered server was
started under its lease; exact container/endpoint is recorded in server.json.
It is a debug transport, not authorization for unlocked device access.

Next offline step: instrument the individual startup checks and their
read-only status values so a subsequent bounded trial can separate wrong
PL identity/reset state from absent RX link. Do not bypass RX-up admission
or force a destination UP. No DMA playback/fault injection was attempted.
