# Observation-to-receipt provenance model — offline

44 PIT tests PASS. New bounded staged producer accepts immutable image bytes
(1..1MiB), nonzero session, before/checked IRQ observations, sample operation
outcome+actual supplied48-byte frame or explicit absence, and final MSR. It
computes image/sample SHA256 itself and derives wire status. There is no caller
image/sample digest or terminal COMPLETE field to override independently.

COMPLETE requires a validated same-session sample frame and verified initial
IRQ transition. Initial IRQ failure forbids sample capture/publication in this
model. READ_FAILED cannot have published samples; PUBLICATION_UNKNOWN can have
committed sample bytes without promotion. Late MSR mismatch/error forces
IRQ_UNPROVEN even with committed samples. Finalization is consumed before final
validation, so invalid final input cannot be retried. Order/type/nonce/image/
stale-sample controls PASS; all decoded results still deny sleep/hardware/DDR.

A roundtrip binds actual local audit-ELF bytes to SYNTHETIC MSR/sample observations
and is labeled synthetic. It is not new hardware evidence or target execution.
Hashes establish only content consistency; image bytes are not authenticated or
validated as running firmware by this producer. Inputs remain supplied claims,
not a trusted hardware trace. Python object state is not tamper-resistant,
cross-thread locking or persistent boot/session uniqueness. No C target hash
producer or trusted MSR/sample-to-record transport has been implemented.
The target audit wrapper metadata gap therefore remains OPEN physically.

No target source/manifest/runtime hook/backend/HW changed. No register/JTAG/UART/
network/reset access. MUST NOT DEPLOY; DDR NOT_ADMITTED. Next safe offline work:
feed actual fake-backend C event outputs into this staged producer and compare
receipt content against observed frame/status, including stale/mixed-session/
late-IRQ negatives, before considering target-side hash/metadata integration.
Independent hung-read recovery and PMU-to-AP0 visibility remain separate blockers.
Reproduce: python -m unittest discover -s tests -p 'test_pit*.py' -v.
