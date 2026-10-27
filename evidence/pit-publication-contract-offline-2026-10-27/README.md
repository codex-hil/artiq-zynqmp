# PIT publication receipt contract — offline

13 PIT unittest cases PASS, including optimized/sanitized C. Four new receipt
cases cover 48 individual changed-byte rejections, high 64-bit nonce, incomplete
commit, wrong version/nonce/length/type, and stable-stale/ABA limitations.
C11 layout assertions pass on host and actual MicroBlaze PMU compile recipe:
48 bytes, complete offset0, version4, nonce8, samples16. Wire decoding is explicit
little-endian <IIQ8I; two exact immutable byte snapshots must match entirely.

This is a caller-supplied receipt decoder, not a physical reader or publisher.
Matching snapshots do not establish freshness, atomicity, visibility, absence
of ABA, authenticated origin, timer frequency or DDR exclusivity. No barrier
was added to the single-context C collector. Physical backend remains false.
The new compile-time assertions do not change intended runtime behavior; prior
linked-code review remains historical and its source pins are not rewritten.

Future publication adapter must use a fresh never-reused session identity,
exclusive ownership and a known invalid initial slot; invalidate before payload,
complete payload before commit, and establish platform-specific memory visibility
and consumer ordering. It must reject reuse/reset ambiguities and interrupted
publication. A double read alone cannot satisfy those obligations. No PMU-local
MMIO callback or DAP workaround is supplied; hanging reads remain unbounded.
Next safe offline work: writer state-machine/interruption tests against this
receipt contract, then target visibility/barrier review before any integration.
No hardware/reset/network access; destructive DDR remains NOT_ADMITTED.

Reproduce: python -m unittest discover -s tests -p 'test_pit*.py' -v.
