# Frozen linked IRQ audit — 2026-10-31

LGPL-3.0-or-later. Offline only, no hardware operations.

41 pinned inputs plus manifest/replay loader: 43 files plus inventory per copy.
Two separate local locations replay under Python -I -B from /tmp with identical
reports. All 50 negative controls reject: each altered file plus missing/extra/
nested inventory/symlink/inventory tamper/wrong independent anchor/--execute.
Existing 113-test result remains dated and unchanged; no gate or implementation
change in this freeze step. Previous frozen mailbox/MMIO copies untouched.

Independent inventory SHA-256: `1b06e40bbdc63f7db960f97dc394593f68ddc612687b96ec977ea1aed4f4a408`.

```sh
/srv/codex-hil-data/artiq-zynqmp/venv/bin/python -I -B /home/codex-hil/.local/state/artiq-builds/pit-irq-frozen-20261031-v1/relocated/snapshot-b/replay.py --inventory-sha256 1b06e40bbdc63f7db960f97dc394593f68ddc612687b96ec977ea1aed4f4a408
```

Loader checks the external anchor before trusting inventory. Modes444/555 are
housekeeping, not security against the owner rewriting loader and files. The full
vendor-containing ELF remains local; public metadata alone cannot replay it.
Content consistency is not provenance, reproducible builds, generic control-flow
proof, live MSR/IRQ/configuration observation, exception exclusion or deployment.
No external PMU RAM consumer is admitted.

Next safe offline step: trace the linked helper's configuration flag at ffdd8b94
to the ELF data/table and maintained BSP initialization source. Record whether the
initial image value and later writes are established, without claiming live state.
Use a separate dependency review; preserve this frozen profile. Runtime hook,
digest origin, no-wake consumer lifetime, exceptions and arbitrary-hang recovery
remain unresolved. No hardware operation follows from passing this audit.
