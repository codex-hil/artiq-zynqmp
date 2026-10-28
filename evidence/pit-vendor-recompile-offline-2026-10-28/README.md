# Vendor-unit rebuild — 2026-10-28

All 60 vendor translation units rebuilt into a fresh v2 directory using the
recorded non-vector/non-lab-guard recipe. -M/-MD captures 235 unique dependencies;
per-unit input sets and hashes match before and after compilation. Output and
-MF paths point only to the new directory. Old objects/dependency lists are intact.

59/60 native code/data inventories match. All 60 native relocation listings match.
The only native difference is xpfw_main.c .rodata: its 102 bytes differ exclusively
inside the eight-byte time and eleven-byte date fields. The source uses __DATE__
and __TIME__ for the firmware banner. Exact changed offsets/strings are recorded
in controls.json; no timestamp normalization or macro override was performed.
The first v1 run stopped on this mismatch and remains local; v2 records differences
rather than treating all units as identical. No complete object equality claim.

report.json records commands, dependency hashes, old/new native section hashes.
recompile.py reuses the earlier custom-comparison helper and refuses overwrite.
This is current same-toolchain evidence, not historical build-time attestation,
compiler independence, rebuilt BSP/archive provenance or final LTO agreement.
No firmware link, hardware access, admission change or host-suite rerun here.

Next safe offline step: link all 70 rebuilt objects against pinned existing
archives and compare resulting PT_LOAD differences, requiring every difference
to be accounted for explicitly before checking the audit layout and flow.
Date/time differences must remain visible. Physical recovery/sleep/AP0 visibility
remain open and are not addressed by compilation.
