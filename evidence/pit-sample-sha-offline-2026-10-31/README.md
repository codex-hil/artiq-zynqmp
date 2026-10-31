# Fixed sample SHA-256 candidate — offline 2026-10-31

LGPL-3.0-or-later. No hardware operations, no integration with capture/root.

New portable C candidate hashes exactly one canonical 48-byte sample record.
API accepts twelve numerical little-endian u32 words and expected nonzero nonce;
validates complete/version/nonce from a private volatile-word snapshot, appends
fixed SHA256 single-block padding (384 bits), and returns standard digest bytes
as eight little-endian u32 groups. No arbitrary-length API or empty/abc input:
those are outside this fixed-format API. No global mutable SHA state.

Input/output must be valid exclusive word-aligned storage; reject NULL, zero
nonce, misalignment and overlapping input/output ranges. Invalid header/session
returns failure without output writes. All input reads precede output; volatile
u32 workspace/output stores avoid aggregate initialization or library clears.
These constraints are not a lock, alias exclusion outside these ranges or memory
protection. The caller must keep input stable during snapshot and correlate it
to publication. The existing publisher does not yet consume this snapshot.

Host optimized shared object matches hashlib for 258 deterministic records,
including all-zero/all-one samples and random nonces/values; invalid header,
nonce, NULL/alignment/overlap controls preserve output. Separate ASan/UBSan
executable checks canonical digest/rejection. Target non-LTO object builds using
existing actual PMU compiler/BSP flags, no undefined symbols and no subword-store
mnemonics in complete object listing. Target frame300 bytes; local swap frame0.
No full call-chain/exception-stack or LTO-linked instruction claim.

Candidate is not bound to capture, publication, terminal record or any runtime
hook. Existing profiles/frozen images unchanged. No digest acquisition proof,
authentication, physical IRQ/sleep/visibility, PMU RAM reader or deployment.
Next safe offline work: a separate snapshot-owning capture/digest/publication API
that hashes and publishes the same private words, including read-failure and
publication-unknown behavior; then actual small C/LTO link/store/stack review.
