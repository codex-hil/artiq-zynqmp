# Physical PMU vector-map snapshot — 2026-10-24

CORRECTION2026-10-27: GPO0 is write-only per UG1087. Readword0 does NOT prove
ROM/RAM selection. Mapping remains UNKNOWN; raw results preserved. See
[write-only correction](../pmu-writeonly-correction-2026-10-27/README.md).


One shared Genesys lease147.988s, cable210383B7F02DA. Candidate and restoration
PASS. PMU-local GPO0 read published version1/raw0 in the guard record; four
coherent nonce-bound external reads agree. This is ONE PMU register sample read
back four times, not four independent time-separated GPO0 measurements. Bit0=0
means RAM-vector remap disabled at that sample, selecting default ROM mapping.
No remap register write, ROM read, private host AP0 alias or retry was performed.
Guard ACK0/unresolved7f remains; IE-only state check passed.

Explicit PMU debugger baseline bootstrap and normal reset/load/TTL/CoreDMA/
analyzerwrap/MonInj/Ethernet restoration PASS192.168.2.3. TwoFS768MiB block
reserves released before restoration; wrapper finished and lease released.
No Si/SD/flash/OTP/Kasli changes. Raw byte inventory includes original UART hashes
with lossless gzip storage; generated Python bytecode intentionally excluded.

This closes the sampled vector-selection gap. ROM event forwarding, fault/reset/
nonmaskable-break behavior and future mapping are not proven. Prior detailed RAM
handler graph/frame inventories remain conditional, not proof of current ROM
exception behavior. Full destructive DDR remains NOT_RUN/NOT_ADMITTED.

Next offline: consolidate what the active ROM boundary prevents proving and work
on independent secondary-core/transaction-history exclusion. Do not repeat this
unchanged successful capture or alter GPO0 to bypass ROM.
