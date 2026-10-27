# Missing/failed MSR observations — fake C trace crosscheck, offline

46 PIT tests PASS. New actual-C fixture -O2 and ASan/UBSan emits six188-byte
frames with explicit observation validity: initial MSR read failure, disable
failure, checked-MSR read failure, final-MSR read failure, unchanged IE despite
successful disable callback, and successful control. First five derive
IRQ_UNPROVEN; control derives COMPLETE. Python producer receipts exactly match
actual C publisher bytes for all six cases, and every decoder denies sleep proof.

Failed read callbacks deliberately fill their output with plausible nonzero MSR
before returning failure. Trace validity follows callback return, not the value.
Five forged-validity promotions rejected. Poisoning bytes from a failed read
still yields IRQ_UNPROVEN, proving they are ignored rather than treated as zero
or success. Truncation rejected. Initial failures prevent all sample reads and
writes; final-read failure can coexist with committed samples but not success.

Trace separately records called/disabled/read counts and valid-before/checked/
final mask. Uncalled/unproven values are absent in the producer even if raw trace
storage contains zeros or failed callback output. The current96-byte error record
uses zero placeholders for unknown MSR but does NOT expose them as proven values;
status remains UNPROVEN. No claim of trusted physical observation follows from
this fake trace. C metadata framing and fixed-vector hashes remain test-only.

No production/target source/manifest/runtime hook changed. No hardware/JTAG/UART/
network/reset/register access. MUST NOT DEPLOY; DDR NOT_ADMITTED. Next safe offline
work: implement explicit callback-return/validity-to-record metadata construction
in C and compare against this independent Python model, keeping externally
supplied hash provenance and physical recovery/visibility unresolved.
Reproduce: python -m unittest discover -s tests -p 'test_pit*.py' -v.
