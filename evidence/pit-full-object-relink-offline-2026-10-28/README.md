# Seventy-object LTO relink — 2026-10-28

All 70 rebuilt objects (ten custom, 60 vendor) linked into a separate audit ELF.
Existing BSP/runtime archives were reused. Explicit input hashes are stable
before/after link; no undefined symbols; existing layout, RO-context-v2 flow and
18+7+3 bound audit gate PASS. Old artifacts/manifests/frozen snapshots unchanged.

The three PT_LOAD descriptors match. Payloads are NOT identical: exactly six
changed bytes in the unique eight-byte time string at 0xffdd2c28 and eleven-byte
date string at 0xffdd2c34. Expected old/new strings come from the vendor-object
comparison. account.py requires unique old fields, exact expected new strings,
identical descriptors and an exact difference set. Additional-byte, wrong-time,
metadata and missing-segment controls all reject. No masking or normalization.
Actual byte offsets/values are in report.json; accounting.json records controls.

Whole ELF hashes differ. This same-toolchain rebuild accounts for current object
sources and timestamps; it does not establish original-time ancestry, independent
compiler trust, rebuilt BSP/libraries, or complete reproducible-build provenance.
No hardware execution, real MMIO backend, sleep/AP0 visibility/recovery proof or
DDR admission. Existing host suite result remains the dated 60-test checkpoint;
new evidence has four direct difference-accounting controls.

Next safe offline step: consolidate this rebuild stage into the qualification
matrix and identify the remaining backend/recovery/visibility blockers, with
separate evidence for source/dependency agreement and physical qualification.
Do not infer permission to deploy from the passing static gate.
