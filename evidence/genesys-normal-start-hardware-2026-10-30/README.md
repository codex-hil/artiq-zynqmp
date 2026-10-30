# Normal Genesys start after user power-on — 2026-10-30

Physical normal runtime PASS at192.168.2.3; verified MAC02:38:3b:7f:02:0d.
One cold-start normal load/test window76.209s: standard PS/JTAG boot selection,
normal PMU/FSBL, local RTIO PL, CPU1worker/CPU0debug runtime; TTL/CoreDMA/analyzer/
MonInj and Ethernet PASS (20/20 ICMP, five TCP connections/1080exchanges,
1129210verifiedbytes). Shared Genesys lease covers load/test; plug reserved
through window, released after; supply remainsON. No flash/OTP/Si/Kasli writes,
PIT audit deployment, DDR writer, powerOFF/cycle or watchdog test.

Earlier passive UART observation found exact Digilent by-id endpoint but no
runtime banner. Initial suspended-PMU recovery helper refused before stop/register/
download because MicroBlaze PMU target absent. Read-only target metadata then
confirmed exact cable+PSU/A53 and generic PMU TAP. Existing cold-start loader
provides the JTAG setup before PMU loading; this distinct cold-start path passed.
The initial refusal is preserved; no forced access or rename-based bypass.

Inputs validated against retained runtime manifest; storage preflight and real
reserve allocations passed. UART is losslessly gzip archived with raw SHA/length.
No diagnostic/guard experiment ran. Owner-confirmed plug mapping and normal boot
now provide a concrete available power-control path plus normal-start evidence,
not proof of autonomous recovery from arbitrary stuck transaction or timed POR.

Next safe offline work: prepare a bounded status-only GLOBAL_CNTRL observer with
exact cable/PSU/AP0/lease pins, no RAM or writes, independent from the disabled PIT
profile. Review and negative controls before a new single physical status window.
