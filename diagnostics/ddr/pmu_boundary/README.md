# AMD PMU core-loop boundary telemetry — offline only

Current checkpoint: explicit sleep/reentry guard was physically captured with
ACK0 on2026-10-23; normal runtime restored. Earlier proposed/unselected/nop-loop
statements below describe historical stages. See [current admission status](../ADMISSION_STATUS.md)
and the2026-10-24 post-guard review; no full DDR admission exists.


`stage_pmu_boundary.py` copies the existing PMU application source into a fresh
output and patches only that copy. The upstream AMD header/license remains
intact. It rejects changed/duplicate insertion anchors and a second patch.

The optional `ARTIQ_PMU_BOUNDARY_TELEMETRY=1` call is placed at the ordinary
`XPfw_CoreLoop` boundary before sleep and scheduler processing. It records a
32-byte static PMU-local BSS object. Without the define this object and call are
absent. It neither disables interrupts nor changes scheduler/PM/secure services.

This is **not quiescence**: interrupts may occur during or after an observation;
reaching a main-loop boundary does not exclude ROM/NMI/error paths or DDR access.
Every observation writes `ack=0` and `unresolved=0x7f`. The sequence/count fields
wrap modulo2^32 and are only diagnostic. A future reader must use a reviewed
coherent capture protocol; sequence parity is not proof of memory visibility or
exclusive ownership. No host address, IPI command or read route is assigned.

The actual patched AMD core compiles with MicroBlaze GCC13.3 and warnings as
errors, both enabled and disabled. Target symbols show exactly32B local BSS only
when enabled. Host C controls verify that observation clears even a forged ACK,
keeps all seven obligations unresolved, and handles count wrap. These are object
and host-model checks, not linked firmware or physical PMU evidence.

Next link an isolated diagnostic firmware using the existing AMD BSP and boot
services, then inspect PMU-local section placement and total capacity. Resolve a
read-only, non-disruptive observation transport before considering deployment.
Do not reuse the failed AP0 private-memory read or guess aliases. A live boundary
snapshot would still be telemetry, never a destructive DDR-test permit.


2026-10-23 request/echo extension (offline): only kind1 OBSERVE. Request and echo
are separate32B local BSS records. Host must set request generation0, write the
payload/checksum, verify readback/order, then publish a new nonzero even generation.
Payload is nonce64+monotonic sequence64+kind1+reserved0. XOR checksum detects some
accidental corruption; it is not authentication or a concurrency primitive.
Firmware checks generation before/after payload and rejects stale sequence or
reused last accepted generation. Echo commits generation last after target mbar1;
status1 means OBSERVED, ack remains0. No quiescence/resume command exists.
Host nonce identifies a cooperating session, not an independently verified boot
identity. BSS zeroing clears state on boot, but reset/boot binding needs separate
proof. IRQ/ROM/exception/ECC paths remain active and unexcluded.

New symbol layout differs from first physical telemetry image: existing fixed
read gate correctly rejects it. New transport/image pins and bounded live echo
qualification are required; no physical request writes have occurred.


## Default-disabled laboratory guard (offline, 2026-10-23)

Only `build_pmu_boundary.py --lab-guard` defines ARTIQ_PMU_LAB_GUARD. Kind2
then enters a no-return guard after the normal generation/nonce/checksum/sequence
validation. Ordinary firmware contains neither guard function nor its64B record
and continues to reject kind2. Never reuse the old telemetry/request addresses
against this new ELF: layout and image pins must be regenerated explicitly.

Guard uses the maintained interrupt-only API, reads MSR before/after and reports
state2 only for `after == (before & ~2)`. State3 means a failed state check.
Both paths publish ACK0/unresolved7f then enter a pure nop/backward-branch loop.
No scheduler, sleep, request dispatch or resume command runs after entry. A full
platform reset/restoration is the only intended exit. Hardware exceptions remain
available; ROM/NMI/error paths and old transactions are NOT excluded.

Host backend tests run guard in a disposable child, inspect committed record,
verify IE-clear/EE-preserved or rejected MSR, then kill ONLY that host-test child.
These tests do not execute PMU instructions or authorize killing/resetting board
processes. Actual linked MicroBlaze flow is checked for its single call to the
interrupt-only helper, local64B record, absence of returns/unexpected branches,
and final instruction-only loop. No physical guard entry has been attempted.
