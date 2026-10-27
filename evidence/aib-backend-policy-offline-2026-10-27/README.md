# Bounded-address backend policy adapter — 2026-10-27

Offline only, no physical MMIO implementation or device access. New C adapter
maps abstract read enum to exactly REQff413030/TYPEff413038/ACKff413040.
Only write path targets REQ, with value equal to initial_request|selected RPUM
mask. Unknown register/mask, preparation reuse and existing selected ownership
are rejected. Preparation reads only; before write it rechecks original REQ/TYPE.
One attempt is consumed even on invalid value or transport failure; no clear,
TYPE/ACK write, alternate address, retry or remap API.

Actual adapter+session+protocol C optimized and ASan/UBSan fixture PASS. Controls:
normal ACK with retainedUSBbits, changed REQ/TYPE before write, malformed write
then valid retry, transport write error, invalid enum without transport access,
stale selected request and prepare replay. Session/core optimized+sanitized
fixtures also PASS. Transport asserts every read address and sole write address.
No synthetic result is a physical acknowledgment or deployment permit.

Trusted local adapter/callback/session storage and serialized caller required.
REQ recheck is not atomic reservation; internal PMU/ROM writers, ABA and concurrent
changes remain possible. Read/tick/write callbacks must themselves terminate;
this code cannot preempt a hanging bus access. Write-error means uncertain
hardware acceptance, not guaranteed held isolation. Boot tokens remain caller
claims. Result is never destructive-test permission.

Control-access contract (not yet proven): selected bits16/17 correspond only to
RPU0/1->LPD directions; OCM/FPD->LPD bits are not requested. Table direction alone
does not qualify actual PMU/DAP/restoration access under isolation. Need positive
source-core hold, competing-writer exclusion, exact linked callback addresses,
clock units and bounds, and a reviewed restoration sequence before a backend can
perform physical writes. Never use existing USB isolation as proof USB DMA halted.

Next offline MicroBlaze compile/final-link audit with this concrete callback table
and fault-injected transport completion/time accounting. No guarded integration,
AIB writes or new HW trial selected; current normal baseline untouched. DDR
NOT_RUN/NOT_ADMITTED.
