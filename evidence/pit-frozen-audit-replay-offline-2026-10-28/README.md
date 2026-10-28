# Frozen relocated audit-input replay — offline

2026-10-28: two local snapshots contain29files/1,806,287logical bytes each:
16custom source/headers,7helpers,3linked artifacts, relative manifest, replay
loader and inventory. Every copied input was verified against its existing pin
before use. The snapshot includes the analyzed ELF, NOT a complete vendor/BSP/
compiler build environment. System Python/stdlib remain external dependencies.

Snapshot-A and relocated snapshot-B replay from an unrelated empty working
directory with Python -E -s -B. Relative artifact paths resolve inside each
snapshot; helpers load from the copied repo/scripts. Reports are identical.
Loader verifies exact inventory/bytes before importing copied audit code and
rejects symlinks and external artifact paths. Eight negative controls PASS:
changed source/helper/ELF, extra root file, extra nested inventory.json, symlink
to original snapshot, external path despite rehashed manifest, execute option.
After restoring negative fixtures, replay is byte/result-identical again.

Initial v1 inventory excluded every filename inventory.json rather than only
the root manifest. Tightened in v2; nested same-name file negative now rejects.
V1 is retained outside Git as historical local input, v2 is the qualified copy.
All files0444/directories0555 after verification. This prevents accidental edits,
NOT tamper resistance: the owner can change permissions/bytes/hashes. Inventory
anchor SHA256 is recorded in qualification.json. No signed provenance claim.

Local replay:
`/srv/codex-hil-data/artiq-zynqmp/venv/bin/python -E -s -B /home/codex-hil/.local/state/artiq-builds/pit-frozen-audit-20261028-v2/relocated/snapshot-b/replay.py`
This executes read-only audit code, not PMU firmware. No command option permits
deployment. Same gate/flow/layout reports remain NOT_HARDWARE/NOT_DEPLOYABLE.
Previously53PITunit tests remain prior evidence; this turn ran actual snapshot
replays and eight negative controls, with no production code change.

No HW/JTAG/UART/network/reset/register access. Runtime/target sources/images
unchanged. DDR NOT_ADMITTED. Next safe offline work: consolidate this checkpoint
into one qualification matrix/handoff separating software/linked PASS from live
NOT_RUN and explicit independent-recovery/AP0-visibility/hash-provenance blockers.
Do not use frozen replay PASS as permission for hardware programming.
