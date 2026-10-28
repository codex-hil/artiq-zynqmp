# Custom-unit recompile — 2026-10-28

Fresh ten-unit compilation in local pit-custom-recompile-20261028-v2 preserves
all original compiler flags except output paths and -MMD changed to -MD.
A dependency-only -M pass records exact current dependencies before compilation;
-MD output records them again afterward. Both sets and hashes agree per unit:
26 unique dependency files total, including system headers. report.json contains
commands, hashes and comparisons. No new link or hardware access was performed.

Every native allocatable PROGBITS section (code/data) and scoped symbolic
relocation listing matches the old fat object for all ten units. A one-byte
native-section mutation is detected. Zero of ten complete object hashes match;
no claim of byte-identical objects, compiler-private LTO IR, debug metadata or
final ELF agreement is made. The first local attempt (v1) stopped when comparing
all relocations including debug; it is preserved. v2 explicitly restricts the
comparison to the native sections named above; no firmware discrepancy is hidden.

New files and dependencies are current observations; original dependency bytes
and vendor/BSP object ancestry remain unproved. This narrow same-toolchain
recompile does not establish independent compiler trust or whole-build
reproducibility. Existing gate/frozen snapshot are unchanged and nondeployable.
No host suite rerun was needed for this evidence-only change; prior 60-test
result remains dated. recompile.py refuses an existing output directory.

Next safe offline step: link the ten new LTO objects with the explicitly pinned
current vendor/archive inputs into a new audit-only ELF, compare loadable bytes,
and run the existing layout/flow checks. Preserve all prior artifacts and pins.
This cannot supply missing MMIO recovery, sleep or AP0 visibility proof.
