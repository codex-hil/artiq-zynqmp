# Frozen owned-mailbox audit — 2026-10-31

LGPL-3.0-or-later. No hardware operations.

27 source/header + eight helper + three artifacts, manifest and replay loader:
40 files plus inventory per copy. Two separate locations replay under Python
-I -B from /tmp and produce identical reports. All 47 negative controls reject:
each changed file and missing/extra/nested inventory/symlink/inventory tamper/
wrong external anchor/--execute. Existing 104-test result is unchanged; no
implementation or gate changed during freezing. Older snapshots remain intact.

Independent inventory SHA-256: `b4b4b0c3270c2d370625f2abc250ee7535424f27ef1304836312b56b30105f98`.

Replay the relocated copy:

```sh
/srv/codex-hil-data/artiq-zynqmp/venv/bin/python -I -B /home/codex-hil/.local/state/artiq-builds/pit-mailbox-frozen-20261031-v1/relocated/snapshot-b/replay.py --inventory-sha256 b4b4b0c3270c2d370625f2abc250ee7535424f27ef1304836312b56b30105f98
```

The loader checks the external anchor before trusting inventory. Owner modes
444/555 are housekeeping, not security against the owner replacing the loader.
The full vendor-containing ELF stays local; published metadata alone is not
sufficient to replay. This verifies content consistency, not trusted provenance,
reproducible builds, whole-path callback/exception safety or physical behavior.
Deployment remains refused. No external PMU RAM reader is admitted.

Next safe offline step: inspect the current PMU MSR observation/interrupt-disable
implementation and specify or qualify concrete audit-only callbacks, including
compiler barriers, return behavior and remaining exception/stack limits. Keep
this frozen profile immutable and use a distinct profile for any new image.
No runtime hook or hardware execution is authorized by these checks.
