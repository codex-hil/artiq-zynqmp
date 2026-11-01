# Abstract fault-slot partial/nested publication model — offline2026-11-01

LGPL-3.0-or-later. Synthetic in-order atomic-word model, not hardware simulation,
exception injection, real PMU RAM reads or evidence of reachable interrupt timing.
No code/vector/runtime/frozen image changes.

Each writer contributes19 events: invalidate, fence,15 payload writes, fence,
commit. Single writer from zero slot:19 incomplete prefixes reject, complete20th
snapshot decodes recordA. Fences are modeled as completed ordering events, not
physical timing or fault recovery. Bus/store faults, reordering and torn individual
u32 writes are excluded assumptions, not solved by this model.

Faithful nonreturning single-core nesting class:20 outer prefixes times20 inner
prefixes=400 cases. Outer never resumes once inner enters.379 states reject,
20 decode fullB, one decodes fullA (outer complete, inner has not stored invalidate
yet). No mixed accepted record in this bounded class. This does NOT establish
physical nesting exclusion, first-fault preservation, freshness or session binding:
inner can overwrite outer, and old committed bytes may remain before invalidation.

Separate deliberately forbidden-resume class inserts fullB insideA then resumesA:
20 cuts; four final slots decode structurally but differ from both source records.
Concrete witness cut7: route2/MSR0x201 fromB, ESR0x102/EAR0x103 fromA; decoder accepts.
This is NOT claimed reachable for the actual nonreturning single-core handler.
It demonstrates that structural validity does not replace ownership/nonreturn
assumptions if outer execution resumes or another writer is allowed to interleave.
Only contiguous-insertion/prefix classes are enumerated, not all possible shuffles.

Witness includes complete abstract trace and final bytes, replayed in tests.
No timestamp/physical event/image/nonce claim; proposed fault-v1 remains unbound.
No sleep/lifetime or recovery conclusion follows. Passing a decoder never permits
external APB access to PMU RAM; independently qualified sleep remains mandatory.

Next safe offline step: review actual PMU configuration/EE/EIP and architectural
entry/reentry restrictions against this candidate, separating documented behavior
from unverified NMI/debug/ROM/platform routing. Do not add a plain flag, change MSR
or exception/vector policy to make model assumptions appear satisfied. Normal
notification policy, ownership, first-fault behavior and recovery stay open.

Full PIT Python suite:155 tests PASS.
