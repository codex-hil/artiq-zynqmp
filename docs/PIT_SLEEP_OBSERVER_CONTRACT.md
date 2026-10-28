# PMU sleep status observer contract — offline only

The parser interprets one caller-supplied GLOBAL_CNTRL sample. It contains no
capture function, MMIO backend, debug call, hardware executor or CLI. Version1
requires exactly version/nonce/address/return_code/value; expected nonzero64-bit
nonce must match and address must be0xffd80000. Booleans are not integers here.
Zero transport return plus a u32 value yields ACTIVE_SAMPLED or SLEEP_SAMPLED
from bit16. Failed transport requires value=null and yields UNKNOWN. Failed
reads carrying plausible output values are rejected. Other register bits are
retained only as caller data and confer no permission. Samples are unauthenticated.

The [UG1087 register definition](https://docs.amd.com/r/en-US/ug1087-zynq-ultrascale-registers/GLOBAL_CNTRL-PMU_GLOBAL-Register)
provides sampled state semantics. It does not reserve a no-wake interval. Every
parser result keeps continuous_sleep_proven, pmu_ram_access_allowed,
recovery_qualified, deployable and hardware_executed false. The separate RAM
admission function always refuses, including caller-supplied success overrides.
There is deliberately no mechanism for a parsed status to open the hardware gate.

Any future status-only physical observer first needs the verified owning station,
exact cable and shared Genesys lease for its entire lifecycle; a reviewed master/
security route and no-wake side effects; one aligned32-bit read of this register;
no writes/RMW, RAM access, PMU debug stop/step/register reads, IPI, reset, policy
changes or automatic retry. It must record transport failure without attempting
a different access route. These are review prerequisites, not a runnable plan or
admission. No physical read is authorized by this document alone.

A sleep sample cannot close exception/reset/debug/wake races across a later RAM
transaction. Safe RAM access requires separate evidence of continuous lifetime
ownership and independent recovery from a stuck transaction; neither exists in
this contract. Host timeout and cooperative IPI are insufficient. No firmware,
mailbox or older physical probe is changed.

Next safe offline work: map the exact candidate's wake/exception/reset/debug
sources to the proposed interval, using existing platform/source audits. Keep
unknown sources explicit and do not disable them to manufacture a quiet result.

## Candidate interval map

[Exact-image review](../evidence/pit-candidate-wake-map-offline-2026-10-28/README.md)
keeps eight event classes unresolved/conditional. Existing RAM exception inventory
is not complete control/dataflow or physical ROM forwarding proof. PM service
capability is distinct from execution while parked. No-wake lifetime and
independent recovery remain unqualified. Next offline consumer state model must
invalidate observations across wake/reset/debug/transport uncertainty.

## Sticky caller-fed lifetime

`pit_sleep_lifetime.Lifetime` holds one nonce. Wake/reset/debug/exception/transport
uncertainty/ownership loss, bad samples and unknown events invalidate permanently;
close cannot restart. Reports are copies and always refuse RAM/deployment.
68 PIT tests PASS including2801 bounded sequences. Delivered-event bookkeeping
does not authenticate events or prove coverage of physical sources. See
[evidence](../evidence/pit-sleep-lifetime-offline-2026-10-28/README.md).
Next safe offline work correlates supplied session/image/terminal receipts
without promoting correlation to physical sleep or recovery proof.

## Supplied terminal/session correlation

`pit_session_correlation.Session` fixes nonce/image SHA at creation and consumes
one terminal validation attempt. Existing decoder enforces terminal/sample
bindings; failures/duplicates invalidate lifetime. Valid content and invalid
lifetime can coexist. No origin authentication or chronological proof is claimed;
all RAM/HW/deployment permissions stay false.72 PIT tests PASS. See
[evidence](../evidence/pit-session-correlation-offline-2026-10-28/README.md).
Next offline replay uses archived C-generated fake-transport traces.

## Archived C-output cross-check

11 fake-transport C output cases replayed in33 event-order variants;44 mixed/torn
controls reject. Archive output SHA verified; no new C/HW execution. Sticky
invalidation and no-admission flags hold for success and failure receipts.
See [evidence](../evidence/pit-session-c-replay-offline-2026-10-28/README.md).
Next safe offline step consolidates this observer/session stage and blockers.
