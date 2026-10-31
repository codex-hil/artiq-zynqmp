# Stackless exception-entry contract checkpoint —2026-11-01

LGPL-3.0-or-later. Contract-only review; no code/handler/vector/image/HW change.

See docs/PIT_EXCEPTION_ENTRY_CONTRACT.md. Local startup/core source hashes and
reviewed official AMD architecture source URLs are recorded in review.json.
Proposal avoids incoming C stack/SDA/argument pointers and never returns; it does
not establish reentry exclusion, target-specific special-register access, trusted
slot memory, notification equivalence, sleep or recovery. MBAR may wait forever
on an outstanding access, so it is not a fault-recovery primitive.

No new executable tests: existing146-test suite remains dated/unchanged/not rerun.
Next safe offline step is standalone unreferenced assembly candidate and static
clobber/relocation/word-store/fence/delay-slot/loop inspection, with no vector
section or link hook. EDR/other unsupported reads must not be added without
separate configuration proof. Current printf gap and physical admission stay open.
