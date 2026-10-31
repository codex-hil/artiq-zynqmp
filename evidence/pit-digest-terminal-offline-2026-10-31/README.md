# Digest-aware terminal adapter — offline 2026-10-31

LGPL-3.0-or-later. No hardware operations/runtime integration.

Separate pure adapter accepts internal digest state, lifecycle result and recorded
MSR observations, builds terminal v1 privately, and copies to initially-zero output
only after consistency checks. No caller-supplied sample digest parameter. Explicit
hash-failure5/rejected0/unknown results are rejected without output writes; no new
terminal-v1 status encoding. Existing terminal builder/publisher and frozen images
are unchanged. This is private result construction, not atomic external publication.

Checks consumed==1, digest_valid0/1, digest presence/nonzero vs sample_outcome,
metadata-builder status vs lifecycle result, initially-zero output and normal v1
validation. Digest absence is permitted only for no-capture/read-failure outcomes;
valid intended digest remains for publication-unknown/complete and final IRQ failure.
Output is checked through legal unsigned-char reads; writes use typed fields and
volatile u32 digest arrays, avoiding struct/u32 strict-aliasing violations. Byte
reads are allowed; no byte/halfword stores found in actual target object.

Host tests exercise four lifecycle statuses, wrong status/hash-failure rejection,
unchanged output on rejection/attempted reuse, and digest-validity disagreement.
Standalone MicroBlaze object frame140, expected pit_terminal_build dependency only.
No linked full-stack/exception or callback control-flow qualification.

Important limit: digest state carries no nonce field, and this adapter cannot
prove it belongs to supplied nonce/MSR observations. Exclusive same-session origin
is a caller premise. It does not authenticate digest/image identity or acquire
observations. A substituted but structurally valid state is outside this guarantee.
The next composition wrapper must own lifecycle state and record observations
from the same invocation, not accept independently supplied states/hashes.

Next safe offline step: distinct composition wrapper owns digest lifecycle and
MSR forwarding state, maps capture/hash failures fail-closed, invokes this adapter,
and publishes terminal only on success. Test same-invocation status/digest/nonce
binding and callback order, then bind/relink a separate root. Current runtime still
uses old composition and no hardware admission is granted. Image input, exceptions,
no-wake reader lifetime and arbitrary-hang recovery remain open.
