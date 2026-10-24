# Fixed read-only AIB observation prepared — 2026-10-24

Offline only, no HW access. Exact AMD lpd_slcr.h and UG1085p421 map REQ/TYPE/ACK
to0xff413030/38/40. Tcl selects exact Genesys cable/unique PSU and performs two
samples of REQ-before,TYPE,ACK,REQ-after (eight total reads),20ms between samples.
No mwr, reset, force, clear, isolation request or TYPE modification exists.
Caller must own shared Genesys lease; no standalone physical launcher is added.
Primary source:
https://docs.amd.com/api/khub/documents/xzMsp_c5sG9J6A3u7NkJYQ/content?Ft-Calling-App=ft

Two tests PASS with actual Tcl and mocked mrd/targets: exact allowlist/count,
zero vs selected-owned state, malformed/truncated/duplicated/address-mutated
frames, request instability and intersample ACK change. Undefined write commands
would fail test. Strict parser preserves raw words, reports selected RPUM0/1 mask
0x30000, and never permits isolation writes or destructive testing. No synthetic
sample is recorded as hardware PASS. hardware_executed=false reflects parser
provenance boundary, not a claim about future callers' source of text.

REQ bracketing catches some changes but not ABA; ACK and TYPE are not atomic.
Two zero samples do not reserve ownership or prove drained transactions. TYPE
is observed, not changed. Every future collector must retain raw failure output,
use fresh helper/artifact pins, shared lease/storage/restoration and stop after
first transport failure. No existing image/helper manifest is silently refreshed.

Next offline integrate this fixed capture into the existing parent-owned trained
observer with an explicit optional manifest, sample before/after guard only if
ordering is useful, and reject unsafe/stale profiles. Then fresh gates and bounded
read-only physical capture, with full baseline restoration. No AIB writes are
part of that step. Full DDR NOT_ADMITTED; ROM/core-release/history gaps remain.
