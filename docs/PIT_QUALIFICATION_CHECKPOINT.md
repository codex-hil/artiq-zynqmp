# PMU/PIT diagnostic qualification checkpoint — 2026-10-28

**Software audit qualified within its scope. New counter profile NOT DEPLOYABLE.
Full destructive DDR test NOT_RUN / NOT_ADMITTED.** No hardware was accessed in
this checkpoint. This document supersedes older *next-step* descriptions, not
raw physical evidence. [Pinned matrix](../evidence/pit-qualification-checkpoint-2026-10-28/matrix.json).

## What passed

| Layer | Result | Scope |
|---|---|---|
| Host behavior | 53 PIT tests last PASS | Actual C optimized+ASan/UBSan with fake callbacks; errors/reentry/hash/frame controls |
| Metadata | C/Python byte agreement | Callback return determines valid MSR; hashes supplied to target remain external |
| Target link/layout | PASS | Fresh non-vector vendor objects; no main/request hook; no HW execution |
| Store width | PASS | Entry and five forwarders have no subword stores; alignment remains conditional |
| Control flow | PASS | 12 direct calls/97 entry branches/five wrappers; static inventory, not liveness/dataflow proof |
| Artifact gate | PASS | 16 custom sources/7 helpers/3 artifact pins; deployment always refused |
| Relocated replay | PASS | 29 files/1.8MB; identical reports from unrelated cwd; eight negative controls |

Internal entry+largest forwarding frame is332bytes; this excludes underlying
callbacks, caller and exception frames. Readonly snapshot modes are not tamper
resistance. Source/artifact pins are not a complete reproducible vendor/BSP/
compiler build or authenticated provenance. A receipt means software intent,
not current IRQ state, sleep residency, AP0 permission or exclusive DDR ownership.

## Historical hardware context

Last documented normal Genesys runtime restoration on2026-10-27 passed physical
TTL/CoreDMA/analyzer/MonInj/Ethernet at192.168.2.3 with lease released. This is
[historical validation](../evidence/guard-context-recovery-hardware-2026-10-27/README.md),
not a fresh health check or IP observation. The Oct24 failed PMU download remains
[retained failure evidence](../evidence/aib-after-guard-hardware-2026-10-24/README.md).
Later recovery does not explain its cause or guarantee recovery from a stuck load.
GPO0 is write-only: historical raw reads do not establish ROM/RAM vector mapping.
Vector-v1 remains prohibited; the new audit image contains no old vector guard.

## Unclosed admission requirements

| Requirement | Current gap | Required evidence before physical admission |
|---|---|---|
| PMU-local capture | No qualified MMIO backend or main/request hook | Reviewed concrete callback/access/fault behavior and exact linked image |
| Receipt provenance | Target hashes external; observations can lie | Bound image/session/sample source and reviewed producer, no caller-success override |
| Mailbox | Probe address is not an allocation | Dedicated symbol-derived record, initialization/lifetime, disjoint owners/stack and exact helper binding |
| Sleep/AP0 | Pre-sleep writes cannot prove residency | Qualified consumer ordering/visibility and terminal entry observation; no running-PMU RAM shortcut |
| Hung-read recovery | Software deadline cannot preempt load | Concrete justified recovery that does not assume the stuck callback returns; current halt/r0 restore is conditional |
| Exception/stack coverage | ROM/EE/NMI/reset, full stack not excluded | Exact platform paths and scoped claims; do not mask arbitrary events to manufacture quiet state |
| DDR exclusivity | Secondary cores/PS masters/posted traffic/epochs open | All-owner exclusion/drain and same-boot/image proof; separate from PIT diagnosis |

No requirement is closed by repeating idle reads, clearing counters, changing
watchdog/reset/AIB policy, guessing private AP0 aliases, reading WO registers or
reusing an old fixed-address helper. No deployment gate is relaxed by this handoff.

## Reviewable continuation

Next authorized safe work is an **offline concrete read-only adapter contract**:
list the exact PMU-local counter loads, record/terminal lifecycle and transport
return semantics; identify which hardware recovery/visibility facts still require
physical qualification. Keep the executable audit profile disabled. Do not add a
DDR writer or select an unchanged hardware retry from this matrix.

Any later hardware action must re-identify the owning station/device, acquire
`/home/codex-hil/.cache/genesys-210383B7F02DA.lock` for the entire JTAG/reset/UART/
AP0/network/test/restore lifecycle, check resource/restore admission and use new
image/helper pins. Other boards and another thread's leases/configuration remain
outside this work. Historical runtime PASS does not waive a new preflight.

## Frozen local replay

`/srv/codex-hil-data/artiq-zynqmp/venv/bin/python -E -s -B /home/codex-hil/.local/state/artiq-builds/pit-frozen-audit-20261028-v2/relocated/snapshot-b/replay.py`

This runs a read-only software audit, not PMU firmware. Local linked artifacts
are required; the public source repository alone is not the vendor build package.
[Replay qualification](../evidence/pit-frozen-audit-replay-offline-2026-10-28/README.md).
