# Coupled C PIT collection/publication — offline

19 PIT tests PASS, including coupled C -O2 and ASan/UBSan. New fixture covers
eight read failures with zero write/barrier callbacks, 30 publication failures
(before/after all15callbacks), successful complete records, invalid entry,
reentrant/duplicate rejection and committed-despite-error ambiguity. Attempt
is consumed before collection; private record and separate internal attempt
states prevent incomplete collection from reaching publication. No retry.

PMU recipe final LTO link PASS/no undefined symbols. LTO inlines the collector
and publisher into pit_capture: frame152, not 88+104+wrapper. Callback/caller/
exception stack remains excluded. Read indirect call ffdcf388; failed read
branches to READ_FAILED ffdcf430 before publication starts ffdcf418. Invalidation
barrier ffdcf460, payload write loop ffdcf4b8, payload barrier ffdcf47c, final
commit ffdcf490. Incoming ABI r5 state, r6/r7 nonce, r8 read, r9 write, r10
barrier, context at entry-SP+28. No concrete MMIO/barrier callback exists.
No target execution, DAP/network/reset or hardware access occurred.

ELF SHA256: 16a46fb6e18c947eeb4b78951a1afd6dda8a5a4853cc4dae3f6f9b9d68ee4d2e
Audit ELF reuses historical prohibited guard objects without runtime call hook;
MUST NOT DEPLOY. Fixed source/object/command evidence is layout context only.
No physical session/ownership/freshness, bounded MMIO, cross-core visibility or
DDR admission established. Normal runtime unchanged.

Next safe offline work: review concrete PMU-local read and publication-memory
access/fault/visibility obligations against vendor BSP and define a minimal
adapter admission checklist tied to code paths. No physical attempt until a
new deployable image and independent recovery/visibility contract are qualified.
Reproduce: python -m unittest discover -s tests -p 'test_pit*.py' -v.
