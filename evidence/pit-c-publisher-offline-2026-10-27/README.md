> 2026-10-27 correction: separately linked array copies contain byte stores,
> unsuitable for PMU word-write-only RAM. See `../pit-pmu-word-write-fix-offline-2026-10-27`.
> Raw artifacts unchanged; this does not imply the full inlined profile had byte stores.

# C PIT publisher — offline

18 PIT tests PASS, including actual publisher C -O2 and ASan/UBSan. The C
fixture covers 60 interruption variants, four successful combinations, exact
callback ordering, high 64-bit nonce, duplicate/reentrant rejection, incomplete
source/null rejection, and callback mutation of source after private staging.
Failure is VISIBILITY_UNKNOWN, with no retry/clear/rollback, including commit
that took effect before the callback reported error. Only offsets, no physical
addresses, are sent to write callbacks.

Actual PMU compiler/BSP LTO link PASS, no undefined symbols. pit_publish at
ffdcf2b4 has frame104, excluding caller/callback/exception stack. ABI incoming
r5 attempt/r6 source/r7-r8 nonce/r9 write/r10 barrier; seventh argument context
loaded at entry-SP+28 (new-SP+132) into r23. Write retained r22, barrier r24.
First write at ffdcf480, invalidation barrier ffdcf494; eleven-word write loop
ffdcf4e8, payload barrier ffdcf500, commit write ffdcf518. Success is returned
only after the final callback returns zero. Private copy is populated before
the first callback, including its last byte in the first call's delay slot.
No concrete barrier opcode/backend is present; linked order is not visibility.

ELF SHA256: 40c4a7c0371ae56d251cd1f28dbf6533580d1530c41f2494a09679dd970f8abc
This audit link reuses historical prohibited vector-v1 guard objects without
any publisher runtime hook. MUST NOT DEPLOY. No MMIO, hardware, reset or network
access occurred; no change to normal runtime. Ownership, never-reused identity,
reset persistence, actual write completion and platform visibility are still
external unqualified obligations. Eight timer reads/hanging MMIO remain outside
this publisher, and destructive DDR is NOT_ADMITTED.

Next safe offline work: couple the C collector and publisher with separate
one-shot state/private storage, test failures across both stages, and reject
publication after incomplete collection. Physical transport remains absent.
Reproduce: python -m unittest discover -s tests -p 'test_pit*.py' -v.
