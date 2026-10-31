# Private capture/digest/publication candidate — offline 2026-10-31

LGPL-3.0-or-later. No hardware operations or runtime integration.

Separate pit_capture_digest API owns a local 48-byte union snapshot. It collects
once, validates/hashes the snapshot with the fixed-record SHA candidate, publishes
the same record using existing publisher, and retains the internally generated
digest in exclusive caller state. Digest validity identifies intended private
bytes even when publication returns visibility unknown; it is not a mailbox
commit, terminal receipt, physical read proof or externally published state.

Reject invalid/nonzero/reused state without mutation. Consume before callbacks;
read failure exposes no digest and performs no publication. Hash failure exposes
no digest/publication. Digest state writes precede valid=1, but no external-reader
barrier/atomic protocol is claimed for that state. It must remain private. Callback
mutation of state/stack and concurrent execution remain forbidden caller premises.
Existing capture/lifecycle/status root and all frozen profiles are unchanged.

Host checks successful byte-exact canonical mailbox/digest, failure at all eight
read positions and all15 publication stages, nested-use rejection and no retry,
nonzero/reused state rejection. Explicit failing-hash/publisher doubles under
ASan/UBSan verify hash failure cannot publish or expose stale digest. These doubles
do not qualify target hash instructions or exception recovery.

Standalone real MicroBlaze object frame156 bytes; expected unresolved symbols
pit_collect/pit_sample_sha256/pit_publish only. No detected subword-store mnemonics
in object listing. Combined non-LTO capture+SHA scoped frame subtotal156+300=456,
not whole stack: linked optimization, caller/collector/publisher/callback/error/
exception paths require separate review. Portable API has no runtime entry hook.

Next safe offline step: distinct small C/LTO audit link retaining this new pipeline
and concrete collector/hash/publisher dependencies, then actual linked store/call/
stack inspection. Do not repin old images or infer terminal-record integration.
Current status composition still accepts caller sample_digest; connecting the new
producer requires a separate lifecycle/composition profile. No HW admission, digest
delivery, trusted image identity, reader no-wake lifetime or recovery is established.

Full Python PIT suite: 121 tests PASS.
