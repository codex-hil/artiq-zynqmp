# Custom LTO relink — 2026-10-28

All ten newly compiled custom fat LTO objects were linked into a new audit-only
ELF, reusing the 60 existing non-vector vendor objects and mapped libraries.
Explicit input hashes agree before and after linking. Resolved archive sets
in old/new maps agree (ten archives). No undefined symbols remain. Existing
layout, ro-context-v2 flow and exact 18+7+3 bound gate checks PASS.

All three PT_LOAD segment descriptors and payloads match: 100020, 2332 and
1024 file-backed bytes respectively (103376 total). Entry/machine, memory sizes,
flags and virtual/physical addresses match. Whole ELF hashes differ; debug and
other non-load bytes are not required to match. This is a same-toolchain custom
recompile/load-image agreement, not a whole-vendor rebuild or trusted provenance.

relink.py refuses an existing output directory; commands/input pins and actual
comparison/check results are in report.json. New manifest/gate reports refer to
local artifacts; original manifest and frozen snapshots remain unchanged. No
hardware, runtime hook, deployment or DDR admission. No new host-suite run:
implementation unchanged, prior 60-test result remains dated.

Next safe offline step: rebuild the 60 vendor units into a fresh directory with
full dependency capture, then compare native sections/relocations before another
controlled link. Vendor/BSP ancestry and physical MMIO recovery/sleep/AP0
visibility remain separate open obligations. No hardware retry is authorized
by this result.
