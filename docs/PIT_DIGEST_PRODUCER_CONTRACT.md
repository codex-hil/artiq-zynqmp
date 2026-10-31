# PIT digest producer contract — proposed, not deployed

SPDX-License-Identifier: LGPL-3.0-or-later

This is an offline contract and host reference, not an implemented target producer.
Existing v1 records and frozen images are unchanged. Hashes establish content
correlation only; they provide no authentication, acquisition provenance, physical
sleep/visibility, interrupt exclusion or ownership. Deployment remains refused.

## Image identity

`image_sha256_le` denotes SHA-256 of the complete final linked ELF file bytes,
including all file headers/debug sections, exactly as pinned in the external
artifact manifest. No stripping or load-segment-only reinterpretation is allowed
under this definition. Each digest's 32 standard SHA-256 output bytes are grouped
into eight little-endian u32 words for the existing terminal record. The word
encoding is not the SHA algorithm's internal word/bit ordering.

Do not embed the final ELF's digest into that same ELF: relinking or patching it
changes the digest. A future admitted host-loader protocol would pass the externally
pinned digest through a separate one-shot input, with image/session binding and
private word-oriented storage. That delivery/trust protocol does not exist yet.
The digest is not a self-measurement or proof that the reviewed image was executed.
No loader writes or runtime hook are authorized by this proposal.

## Sample identity

Hash exactly 48 canonical bytes, no prefix/domain string, no padding or pointers:

| Offset | Bytes | Meaning |
|---|---|---|
| 0 | 4 | complete = 1, little-endian u32 |
| 4 | 4 | version = 1, little-endian u32 |
| 8 | 8 | nonzero session nonce, little-endian u64 |
| 16 | 32 | eight returned PIT values, little-endian u32 in acquisition order |

The producer must receive the expected nonce separately, reject mismatches, and
hash the exact immutable private snapshot used by sample publication. This is the
logical completed record, including complete=1, not the mailbox while its commit
is zero or partially written. Do not hash raw C structure storage unless target
layout/endian/padding are established. Prefer explicit canonical u32 serialization.
Do not re-read PIT counters to compute the hash; do not read an externally visible
mailbox to reconstruct the source. The host reference accepts already supplied
immutable bytes and cannot establish how they were acquired.

## Ordering and failure

A future separate target pipeline must: collect all eight values into owned storage;
freeze/validate the complete snapshot and nonce; calculate SHA-256 from those bytes;
publish those same bytes with the existing word/fence/commit protocol; perform final
MSR observation; build/publish the terminal record with the internally produced
sample digest; then enter the terminal loop. No callbacks may mutate the snapshot
or digest state. Complete digest computation before final MSR observation so its
execution is included in the observed interval. Final observation still cannot
prove the later receipt publication or sleep interval has no exception/wake.

Collection failure or no capture: no sample digest, terminal hash field zero.
Publication failure after complete collection: a valid digest may identify the
intended private snapshot, but status remains publication/visibility unknown; it
does not assert any complete mailbox record. Initial/final IRQ policy failure
remains failure even with a digest. Target hash failure must not retain a prior
session's digest or silently accept the caller-supplied sample hash. Define a
separate explicit failure outcome before changing the existing target API.

Current `pit_capture` keeps its snapshot local and does not expose a digest.
Current `pit_status_compose_model` forwards caller `sample_digest` based on callback
counts; that is not a producer or a correlation proof. A new API/profile is needed.
Existing collector/publisher/lifecycle or frozen audit pins must not be silently
repurposed. Future target SHA implementation must have known vectors, boundary
length tests, no byte/halfword stores in PMU RAM, bounded stack including SHA state,
no unreviewed library clearing/copy path, and actual linked instruction review.

Next safe work is a separate offline SHA-256 implementation/API candidate with
canonical test vectors, followed by a revised private snapshot pipeline. Hardware
entry, digest delivery, recovery, exception paths and consumer lifetime remain open.
