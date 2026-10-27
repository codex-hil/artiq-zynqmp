# Backend callback/address audit after actual PMU LTO link — 2026-10-27

Offline only, no firmware deployment/MMIO transport. Actual PMU recipe rebuilt
three components and retained session arm/execute/backend_prepare in separate
AUDIT_ONLY ELF. Main/guard do not call them. Local layout check PASS.

Exact linked callback assignment checker PASS: read_regffdcbf04,
write_requestffdcbf74,ticksffdcc05c stored at target backend offsets20/24/28.
Read enum map atffdd42c4 contains REQff413030,ACKff413040,TYPEff413038.
Actual ELF mutation test rejects table/target/store changes. This is build-specific
assignment verification, not proof all pointer/control paths are safe. Underlying
read32/write32/ticks transport callback addresses remain unbound.

LTO stack reports: execute172,snapshot48,read_reg28,write_request44,ticks28,
prepare56,arm0. Internal read path248bytes excludes caller/transport/library
cost. Write path216 and tick path200 similarly conditional. No complete bound.
Link warns pipe ignored and serialLTRANS only; compile/link succeeded. No original
build modified. Artifact hash and commands retained; no image is admitted to HW.

Next offline timing fault injection must cover backend REQ/TYPE rechecks. The
strict protocol checks time before invoking write_request, but adapter executes
two further reads before physical write callback. Deadline can expire during
those calls; current code must not be claimed to prevent every post-deadline
write. Transport callbacks may block and uncertain writes must never be undone
blindly. Clarify this effect/budget boundary before adding any actual MMIO backend.

Source-core hold, PMU/ROM competing writers, physical OCM/debug/restoration access
and full-master coverage remain open. Current normal runtime unchanged. DDR
NOT_RUN/NOT_ADMITTED. No unchanged HW retry or AIB write selected.
