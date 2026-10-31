# Separate linked IRQ audit gate — 2026-10-31

LGPL-3.0-or-later. Offline, no hardware operations.

Actual linked image passes a distinct exact instruction/storage profile:
20 bodies / 1008 instruction words. Includes IRQ-binding root, observer,
disable callback and both linked C-helper paths/configuration-read address,
as well as existing MMIO/publication/terminal scopes. Owned storage and mailbox
layout are checked against this image's new addresses. No old profile is repinned.

113 Python tests PASS: 12 labeled IRQ/helper mutants, mutation of every one of
1008 scoped words, stale listing/storage controls and 41 changed-file controls.
Synthetic fixtures preserve original reviewed words but are not hardware tests.
Actual ELF report/manifest separately record the positive check. The gate pins
30 project C/header files, eight helpers and three artifacts. Vendor source/BSP
build provenance is not qualified by those project source pins. The full linked
ELF is pinned but kept local. Consistent bytes are not reproducible-build proof.

Both helper instruction paths clear IE2 statically; neither the live configuration
flag nor behavior under exceptions is observed. No generic CFG/dataflow proof,
whole-stack/exception safety, live interrupt policy, no-wake reader lifetime or
arbitrary-hang recovery follows. Deployment and --execute are refused. No runtime
hook, authenticated digest producer or external PMU RAM consumer is admitted.

Next safe offline step: freeze this distinct 41-input closure plus manifest/loader,
relocate and replay with independent inventory anchor and tamper/refusal controls.
Earlier frozen images and evidence remain unchanged.
