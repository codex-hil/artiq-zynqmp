# Source/artifact-bound composition audit gate — offline

2026-10-28:53PITtestsPASS. Actual new full PMU audit ELF/source/helper/layout/
composition-flow checks PASS with16custom source/header pins,7helper pins and
3artifact pins. Artifact hashing and structural checks use the same byte copies.
Flow includes raw no-subword checks for entry and all five forwarding functions.
No old v3 manifest or old deployment wrapper was relaxed or repinned.

26independent input-change controls (16customsources+7helpers+3artifacts) reject
before structural check invocation. Schema/profile/extra execute flag, claimed
hardware/deploy flags and missing closures reject. CLI --execute is an argparse
error with exit2. Explicit deployment function ALWAYS refuses; existing hardware
guard preflight also rejects this schema before physical tooling.

Synthetic files test hash-layer rejection only; actual audit.json independently
checks the real linked ELF. Pins cover custom sources/helpers, NOT a complete
reproducible vendor/compiler/BSP build closure or signed provenance. Hash+structure
PASS cannot authenticate callbacks, actual running image, session freshness,
current IRQ, sleep, cross-core visibility, exception paths or hung-read recovery.
Source files are not an atomic filesystem snapshot; no execution path depends on
this result. No manual command or separate tool is authorized by this gate.

Outputs keep deployable/backend/hardware/DDR false. No runtime hook, physical
backend, target source/image or mailbox changed. No JTAG/UART/network/reset/
register/HW access. MUST NOT DEPLOY; DDR NOT_ADMITTED. Next safe offline work:
freeze a local self-contained read-only audit input snapshot and re-run checks
on copied inputs to verify closure/relocation before a qualification handoff.
Independent MMIO recovery, AP0 visibility and target hash provenance remain OPEN.
Reproduce: python scripts/pit_composition_audit_gate.py --manifest
 evidence/pit-composition-bound-gate-offline-2026-10-28/manifest.json
and python -m unittest discover -s tests -p 'test_pit*.py' -v.
