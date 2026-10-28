# RO-context rebuild checkpoint — 2026-10-28

Offline rebuild-review stage complete. Nine evidence rows and seven unresolved
admission obligations are in matrix.json. Each evidence reference has a SHA-256.
verify.py checked all references, three-segment/six-byte difference accounting,
four negative controls and the separately anchored relocated frozen RO replay.
verification.json records PASS; this does not admit hardware. Earlier matrices
and original artifacts remain immutable. The dated 60-test suite is not rerun or
promoted to physical evidence. No hardware was accessed.

The full 70-object relink is not identical: six timestamp bytes differ. Existing
BSP/runtime archives were reused, so complete build provenance remains incomplete.
The frozen snapshot contains the prior audit image, not a repinned rebuilt ELF.

Next safe step: offline feasibility review of non-MMIO PMU sleep observation and
independent hung-load recovery using local manuals/source. Before any HW plan,
show how sleep is established without accessing a running PMU's RAM and how a
stuck callback can be recovered without assuming it returns. If no supported
mechanism can be established, retain the block and name the required human or
physical intervention. Do not deploy or repeat an unchanged physical experiment.
