# Frozen concrete digest-root audit — 2026-10-31

LGPL-3.0-or-later. No hardware operations.

52 pinned inputs plus manifest and replay loader:54 files plus inventory per copy.
Two separate local locations replay under Python -I -B from /tmp and return
identical reports.61 negative controls reject: every altered file, missing/extra/
nested inventory/symlink/inventory tamper/wrong external anchor/--execute. Existing
133-test result remains dated and unchanged; no implementation/gate changes in
this freeze step. All prior frozen MMIO/mailbox/IRQ snapshots remain untouched.

Independent inventory SHA-256: `2812eff93bc6cef8b2bd05f151d7233cde3c3ba5a4121f7c7b0346534a6cb782`.

```sh
/srv/codex-hil-data/artiq-zynqmp/venv/bin/python -I -B /home/codex-hil/.local/state/artiq-builds/pit-digest-root-frozen-20261031-v1/relocated/snapshot-b/replay.py --inventory-sha256 2812eff93bc6cef8b2bd05f151d7233cde3c3ba5a4121f7c7b0346534a6cb782
```

The external anchor is checked before trusting inventory. Read-only444/555 modes
are housekeeping, not security against the owner replacing loader and inputs.
The complete vendor-containing ELF stays local; public metadata alone cannot
replay without those artifacts. Consistency is not independent build provenance,
reproducibility, generic control-flow or hardware behavior qualification.

No deployment/main request hook, trusted image-digest delivery, external PMU RAM
consumer, exception exclusion, no-wake sleep lifetime or arbitrary-hang recovery
is admitted. Earlier physical results are unchanged and not rerun here.

Next safe offline work: audit normal-path stack/call graph with exact concrete
indirect callback bindings from this ELF, replacing scoped frame subtotals with
an explicitly bounded normal-path analysis. Retain separate open obligations for
exceptions/interrupt/debug/error paths, caller entry frames and hung callbacks.
Do not treat a normal-path bound as physical admission or a guarantee of recovery.
