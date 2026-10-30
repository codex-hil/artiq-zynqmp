# Concrete raw PIT MMIO callback — offline, 2026-10-30

New pit_mmio_read permits only four PMU-local COUNTER addresses, NULL context
and nonnull output. It performs one volatile const32-bit load, then one word
output copy. Zero return says the load returned; it is not bus-fault detection or
hang recovery. pit_ro_adapter supplies the ordered eight-read budget. Caller
owns a valid disjoint output buffer; the callback is not an isolation sandbox.

78 PIT tests PASS. Host fixture maps an anonymous process-private page at the
register-shaped virtual address; no physical memory/device mapping. Verifies
four allowed addresses through two adapter rounds, ninth rejection, invalid/WO/
wrong-bank/unaligned addresses, null output/context rejection and unchanged page.
Compilation refuses absent MicroBlaze/audit opt-in. Native MicroBlaze object has
one lwi/one swi/one return, no calls/subword stores/undefined symbols. Fat native
object is not full linked LTO or full dataflow proof. No target deployment or HW.

Old RO source/gate/snapshot pins unchanged; new files are not automatically part
of that closure. Backend remains audit-only and unintegrated into actual runtime.
Review docs/PIT_ONE_SHOT_TRIAL_PLAN.md before any future trial. Next safe offline
step integrates the callback into a fresh audit LTO profile and qualifies its
additional call/address/store/stack footprint without extending old gate admission.
