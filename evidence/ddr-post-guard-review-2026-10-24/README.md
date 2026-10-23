# Post-guard DDR exclusion review — 2026-10-24

Offline review of retained evidence and exact candidate source. Physical record
PASS narrows the PMU gap; none of the seven whole-system obligations can yet be
closed without qualifications. review.json binds inputs and states each gap.
No live device access, no fresh health check, no change to admission policy.

A concrete next boundary is the PMU hardware exception path, because the guard
intentionally preserves EE. Exact candidate xpfw_start.S:24 branches to
XPfw_Exception_Handler; xpfw_core.c:495-510 prints diagnostics, performs persistent
and PMU error-register RMW operations, then loops without sleep. Software
exception path xpfw_start.S:75-90 stores ESR/EAR/error registers and loops too.
Thus proving the ordinary guard terminal alone does not close all future PMU
execution paths. Exception loops may again prevent external RAM observation;
missing readback must never be interpreted as retained guard residency.

Source observations are not complete linked call-graph or ROM/reset reachability
proof. Next offline action: extract exact linked hardware/software exception
vectors, helpers and transitive call/data footprint; classify indirect/ROM exits
as unresolved. Preserve exception reporting. Do not clear EE, mask error inputs,
change error policy or generate a DDR permit to bypass this gap.

Separately, secondary-core future release and PS transaction history/drain need
their own same-boot exclusion argument. Another idle snapshot or repeating the
successful guard capture will not resolve those obligations. No destructive DDR
backend is selected. Retain separate low/high windows and full restoration flow.
