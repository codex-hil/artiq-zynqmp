# C terminal-intent record framing/publication — offline

38 PIT tests PASS. New actual C -O2/ASanUBSan fixture:108 interruption controls
(27callbackpositions x before/after-effect x fresh/previous slot), four complete
session/slot combinations, all four status values, invalid COMPLETE and nested
entry rejection, mutation of source digest after staging. Exact offset/word-only
callback order verified: invalidate/barrier/23payloadwords/barrier/commit.
Failure is UNKNOWN with no retry/rollback, including error-after-commit.

C11 assertions host+MicroBlaze: struct96bytes, nonce16, MSR24, image32, sample64.
Hash byte strings are represented in C as eight little-endian u32 groups each,
not byte arrays. Publication freezes words before callbacks; array copies use
volatile u32 to respect PMU RAM word writes. Fixture serializes the actual C
writer output to96explicit little-endian bytes; unchanged Python receipt decoder
accepts it as IRQ_UNPROVEN with sleep/hardware/admission flags false.

The publisher does NOT compute or authenticate hashes and does not inspect the
sample payload. Provided nonzero digests are framing fields only. Python checks
sample/hash/session binding separately. A C framing success must never replace
that check. CAPTURE_COMPLETE field consistency (IEclear/exactMSR/samplehashpresent)
is checked, but real execution, hash provenance, session lifetime and sleep are
NOT proven by those fields. Error records may refer to committed sample data.

MicroBlaze non-LTO standalone linked opcode check PASS/no subword stores/no
undefined symbols; frame152 excludes callbacks/caller. Standalone text at zero,
MUST NOT DEPLOY. No integration with PMU main, lifecycle, terminal or mailbox.
Existing v3 runtime audit sources/artifacts were not extended with this component.
No physical MMIO adapter/barrier or target digest producer exists. No hardware
JTAG/UART/network/reset/register access. DDR NOT_ADMITTED.

Next safe offline work: couple lifecycle status to the separate writer through
fake callbacks and confirm publication errors cannot promote IRQ/sleep status;
keep receipt content/commit distinct from actual terminal entry and residency.
Reproduce: python -m unittest discover -s tests -p 'test_pit*.py' -v.
