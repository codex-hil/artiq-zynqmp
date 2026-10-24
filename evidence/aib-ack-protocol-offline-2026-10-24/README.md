# AIB acknowledgment protocol reference — 2026-10-24

Offline model only: no MMIO, firmware integration, register request write or
hardware receipt. Four protocol tests and unchanged vendor-timeout host test PASS.
Modeled mask subset is RPUM0/RPUM1 bits16/17,0x30000, from exact lpd_slcr.h.
OCMS bit26, LPD_DDR bit27 and all other masks are rejected by the model. This is
scope restriction, not proof the subset suffices for DDR ownership.

Fresh selected request and ACK bits must initially be zero; nonce-like sequence
and boot epoch must match. Request preserves unrelated bits. Poll budget finite;
ACK accepted only if every selected bit is set in the same sample. Partial ACK,
changed request/type/epoch or exhausted budget yields FAILED_HELD_MODEL. Successful
state is DRAINED_HELD_MODEL, never a write permit. No release/resume action exists;
request word remains held even on failure in the reference. There is no actual
hardware request, so this is not evidence physical isolation was held.

AMD UG1085v2.5 Table16-17p420: RPU0/1 master paths to LPD are distinct from
LPD->OCM and FPD->LPD/OCM paths. A subset request does not intentionally select
those OCM directions. It may still affect clients routed through the selected
masters, and full DAP/PMU/control access dependency has not been proven. No live
AIB response type or ownership state has been captured. p421 recommends setting
TYPE at boot and holding REQ until ACK; do not rewrite TYPE during diagnosis.
Primary source:
https://docs.amd.com/api/khub/documents/xzMsp_c5sG9J6A3u7NkJYQ/content?Ft-Calling-App=ft

Before any isolation candidate: map all affected routes and restoration access,
use read-only snapshots of actual REQ/ACK/TYPE to reject preexisting ownership,
bind request/ACK to actual boot/image and positive source halt, add elapsed-time
and exception handling, exact bounded readback and failure restoration. Sampling
zero before a request does not prove exclusivity against other agents. Existing
shared device lease is necessary but does not stop PMU/ROM internal writers.

Next offline: prepare fixed documented REQ/ACK/TYPE read-only observation schema
and decoder with malformed/mismatched/owned-state controls. No register writes
or physical attempt yet. ROM/future-core-release/other masters remain unresolved;
DDR NOT_ADMITTED. Normal baseline unchanged, no fresh health check.
