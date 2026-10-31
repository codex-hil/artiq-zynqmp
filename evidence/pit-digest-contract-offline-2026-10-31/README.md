# Digest contract checkpoint — 2026-10-31

LGPL-3.0-or-later. 117 Python tests PASS. No hardware operations.

Contract: docs/PIT_DIGEST_PRODUCER_CONTRACT.md. Host reference:
scripts/pit_digest_contract.py. Synthetic vector in vectors.json. Tests cover
exact immutable record size/version/commit/session nonce, all 32 sample-byte
single-byte mutations, digest little-endian word packing, standard abc SHA-256,
and input rejection. Python hashlib is a reference only, not a PMU implementation.

Finding: current capture snapshot is private/local; caller sample_digest is not
computed from it. New target API/pipeline required. Hash final ELF externally to
avoid self-hash circularity, and design a separate future input binding; no loader
or request protocol exists. No target producer, authentication, physical claim,
deployment or external RAM consumer admission. Existing frozen profiles unchanged.
Next offline step: separate bounded SHA-256 candidate and canonical vectors/store/
stack qualification before integrating with a revised private snapshot pipeline.
