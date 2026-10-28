# Frozen RO-context v2 replay — 2026-10-28

Two isolated local copies of the exact 18-source/header, seven-helper and three
artifact audit closure produce byte-identical passing reports under Python -I -B
from /tmp. No imports from the live repository are needed. Thirty files plus the
inventory are retained per copy. Historical forwarded-v1 snapshots are unchanged.

Nine independent negative controls reject source/helper/ELF/manifest tampering,
a missing file, extra file, nested inventory.json, symlink and --execute. See
verification.json. These are additional replay controls; the host suite remains
60 PIT tests (no C or gate implementation changed at this checkpoint).

Local copies:
/home/codex-hil/.local/state/artiq-builds/pit-ro-frozen-audit-20261028-v1/snapshot-a
/home/codex-hil/.local/state/artiq-builds/pit-ro-frozen-audit-20261028-v1/relocated/snapshot-b

Replay using the project Python with -I -B and the chosen copy's replay.py.
Before replay, compare inventory.json SHA-256 against this separately recorded
anchor: dad1b193758a9682a1292e1485e512e73d5f19af5991a3adbab0d5b4f69e4578.
The loader validates content against inventory; an attacker able to rewrite both
can forge that local check. File modes 444/555 are not a security boundary.
Full vendor-containing ELF stays local; public evidence includes only metadata,
inventory, loader and reports. It cannot replay without the local snapshot.

No hardware, deployment, DDR admission, trustworthy full build provenance,
physical MMIO backend, bounded recovery, sleep or AP0 visibility is established.
Next safe offline work: review build.json against the frozen source/object/link
inputs and inventory the unpinned compiler/vendor/BSP provenance dependencies.
Do not claim a reproducible build from source hashes alone.
