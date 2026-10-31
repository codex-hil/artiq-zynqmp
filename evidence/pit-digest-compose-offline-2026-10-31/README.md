# Same-invocation digest composition — offline 2026-10-31

LGPL-3.0-or-later. No hardware operations or runtime integration.

New separate plan has NO sample-digest input. Composition owns local digest state
and forwarding MSR observations from the same lifecycle call. It snapshots nonce,
image digest words and callbacks/contexts before callbacks, reserves plan consumed,
runs digest lifecycle, builds terminal via checked adapter and publishes only on
metadata success. Image identity remains externally supplied, not authenticated.
Private plan/stack/callback exclusivity is a premise, not a hostile-code boundary.

Initial/read/final policy failure statuses are validated using recorded callback
returns. Hash failure refuses terminal v1 entirely, including when final IRQ failure
has overridden lifecycle status: eight successful reads without valid digest are
not mapped into read-failure or complete metadata. No request hook/terminal sleep
is added. Caller terminal callback is not invoked: lifecycle terminal is deferred,
and this is a returning offline model, not physical sleep/visibility proof.

Host full suite125 tests PASS; strengthened focused composition test also PASS.
Integration checks six scenarios with actual C SHA and failing-hash double across
six distinct64-bit nonces: byte-exact terminal publication, image words, canonical
sample hash, status, final MSR before receipt, initial/read/sample-publication/final-
MSR/receipt failures and one-shot no-retry. Hash failure with final MSR failure
must still leave zero terminal record and no receipt writes. Receipt failure keeps
publication status unknown, not success. No target physical behavior tested.

Actual standalone MicroBlaze compile: composition frame244; observe44, disable28,
read/write/barrier32, defer0. Expected unresolved dependencies only digest lifecycle,
digest terminal adapter and terminal publisher. No detected subword stores in
complete object. Standalone composition244+lifecycle128+capture156+SHA300=828
is a scoped subtotal, not linked/caller/callback/exception whole-stack proof.

No read-order adapter is bound by this portable API. All callback forwarding is
synchronous and returning; hung callback recovery remains external. Concrete MMIO,
IRQ, owned mailbox, read-order adapter and nonreturn terminal must be bound in a
new reviewed root, preserving old profiles. Next safe offline step: distinct root
with exact device-independent callback binding, a fresh small C/LTO image, and
actual instruction/store/stack review before any hardware consideration. Existing
runtime/frozen images unchanged; no deployment or external PMU RAM reader admitted.
Image digest delivery, exceptions, no-wake lifetime and recovery remain open.
