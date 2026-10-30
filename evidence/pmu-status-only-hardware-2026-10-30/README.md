# Single PMU sleep-status physical observation — 2026-10-30

ONE aligned32-bit XSDB PSU/AP0 read of GLOBAL_CNTRL0xffd80000 on exact Genesys
cable210383B7F02DA. Returned0x00018812, MB_SLEEPbit16=1 at sample time. No PMU RAM,
register write/RMW, stop/step/reset, firmware/PL programming, IPI or power change.
Shared Genesys lease and unique plug reservation held throughout; both released.
Existing normal runtime remains at192.168.2.3/MAC02:38:3b:7f:02:0d. Ethernet
identity/20ICMP/fiveTCPconnection tests PASS before and after observation.

Plan source hashes unchanged.76 PIT tests PASS, including four Tcl mock methods
checking exact one-read access, identity/ambiguity/no-read refusals, malformed
response/no retry and argument validation. Initial fixture global-variable
collision was fixed before physical execution. No hardware retry was made.

This validates one observed status-only transport window and sampled sleep, not
continuous residency, absence of wake/reset/exception, target hash provenance,
arbitrary stuck-read recovery or permission for external PMU RAM. The parser's
hardware_executed=false describes its offline interpretation function; the outer
capture result correctly records physical hardware_executed=true. Receipt/RAM/
PIT deployment gates remain closed. No DDR test ran. Old physical evidence intact.

The narrow status-only capture stage is complete. Before any counter diagnostic,
separately qualify real PMU-local backend, terminal/no-wake lifetime, symbol-owned
mailbox and independent recovery/restoration. Successful normal status polling
cannot satisfy those prerequisites; do not repeat it as exclusion proof.
