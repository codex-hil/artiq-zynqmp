# Frozen word-init MMIO audit replay — offline, 2026-10-30

New20-source/header +7-helper +3-artifact closure frozen into two independent
locations.32 files plus inventory per copy (including manifest and replay loader).
Both replay from /tmp under Python -I -B and return identical audit reports.
39 negative controls reject every changed frozen file plus missing/extra/nested-
inventory/symlink/inventory-tamper/wrong-anchor/--execute cases. No HW access.
Previous89-test suite result remains dated; no implementation or gate changed.

The loader requires an independently recorded --inventory-sha256 argument and
checks it before trusting inventory. The recorded anchor is:
85e9e184062b1817dd6dcb5aec4650a2fc14709ac99a2a0f8de7fd3678b89605

Example:
/srv/codex-hil-data/artiq-zynqmp/venv/bin/python -I -B /home/codex-hil/.local/state/artiq-builds/pit-mmio-word-frozen-20261030-v1/relocated/snapshot-b/replay.py --inventory-sha256 85e9e184062b1817dd6dcb5aec4650a2fc14709ac99a2a0f8de7fd3678b89605

Local copy paths in verification.json. Frozen file modes444/555 are housekeeping,
not a sandbox against an owner replacing loader+inputs. Full vendor-containing
ELF remains local; public metadata/loader/inventory alone cannot replay without
those artifacts. freeze.py refuses overwrite; older snapshots untouched. Exact
pins establish consistency, not independent provenance, whole-path callback/
exception qualification, physical sleep/recovery or deployment permission.

Next safe offline step: define an image-owned sample/terminal mailbox allocation
and verify symbol-derived boundaries/alignment/nonoverlap, without installing a
runtime hook or allowing external RAM reads. This advances the existing one-shot
plan's result-allocation requirement; consumer lifetime and recovery stay open.
