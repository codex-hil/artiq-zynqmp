# Separate terminal-intent receipt — offline schema and decoder

37 PIT unittest cases PASS. New decoder accepts only two identical96-byte
immutable snapshots with committed version1/magic, status1..4, matching nonzero
session nonce, expected nonzero image SHA256 and sample-byte SHA256 (or explicit
absence). CAPTURE_COMPLETE additionally requires a valid same-session sample
record and exact IE-clear checked/final MSR equality. Error statuses never promote
sample data to capture success, including when committed samples already exist.
Sample bytes alone, stale/mixed image/session/sample hashes and incomplete data
are rejected. A supplied hash is content binding, not origin authentication.

ALL outputs set sleep_proven=false, hardware_executed=false,
physical_backend_ready=false and destructive_test_allowed=false. Even a valid
CAPTURE_COMPLETE receipt means a supplied software report, NOT sleep residency,
a hardware access proof or DDR isolation. A write issued before sleep cannot
prove that the later sleep instruction executed. Double reads do not exclude
stable stale bytes, ABA or unobserved writes. Failure plus committed samples
remains an explicit supported observation; never infer rollback/cancellation.

No target C struct/writer/MMIO callback or firmware hook was added. The versioned
schema is separate from the48-byte sample record and no existing physical parser
was extended to accept it. Current v3 target image/source pins unchanged by this
host-only decoder. Real image-hash provenance, boot/session identity, physical
publication/consumer ordering and independent stuck-read recovery remain OPEN.
No live register/JTAG/UART/network/reset access; MUST NOT DEPLOY/DDRNOT_ADMITTED.

Next safe offline work: C layout assertions and fake-memory publication for this
separate record, with interruption/error-after-commit tests and same no-sleep-
proof semantics; do not turn a completed receipt into permission for AP0 access.
Reproduce: python -m unittest discover -s tests -p 'test_pit*.py' -v.
