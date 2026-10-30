# Exact MMIO instruction pins and hostile mutations — offline, 2026-10-30

Separate checker pins nine reviewed function address/size/SHA bodies (712 words)
from the actual linked MMIO audit ELF. Each instruction must match the same ELF
load bytes and disassembly; exact ranges/unique instruction rows required. This
is byte consistency for one build, NOT a generic CFG/dataflow or semantic proof.
No claim of independent compiler trust or physical execution is made.

82 PIT tests PASS. Sixteen labeled binding/context/adapter/consumed/address-bank/
WO-alias/raw-load/output-width/budget/terminal mutations reject even with matching
synthetic ELF and disassembly. Additionally every one of712 scoped instruction
words was individually replaced and rejected. Stale disassembly, missing/duplicate
symbols, changed size and duplicate instruction rows reject. Synthetic positive
fixture uses archived actual bodies; actual full ELF independently passes pins.

IMPORTANT NEW LIMIT: unconditional subword-store checking failed in library
memset atffdd2814 (sbi); another sbi is atffdd28c8. These byte paths remain in the
linked library. Project entry/raw/five-forwarder/terminal checks pass, but library
store-width qualification is explicitly FALSE in check.json. Pins do NOT waive
this. Actual entry calls memset atffdcf6b0, with count48/r7, destinationSP+28/r5.
That may select only word loops for aligned stack, but no full entry-argument/
alignment/lifetime proof has been established. Do not infer whole-path safety.

The initial82-test run plus actual checker rejected the library; it was not a
hardware failure. The final checker deliberately separates exact nine-body pins
from eight project-function word-store checks and reports the unresolved library
obligation, rather than claiming a global no-byte-store pass. No existing gate
was expanded; deployment stays refused. No HW access occurred.

Next safe offline fix: replace the48-byte automatic aggregate zero initialization
in pit_capture with explicit volatile32-bit word initialization, then rebuild a
new MMIO audit LTO artifact and verify the entry no longer calls memset. Preserve
old artifacts/pins and demonstrate the width condition without relying on a
library alignment branch. Source and complete gate closure must then be new.
