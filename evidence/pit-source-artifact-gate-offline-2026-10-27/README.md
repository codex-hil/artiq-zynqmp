# Source/artifact-bound offline audit gate

Actual fresh PMU ELF/layout/flow with current10source+6helper hashes: OFFLINE
AUDIT PASS. Same bytes are hashed and structurally checked, avoiding a second
artifact read during this audit. Gate CLI offers only --manifest, no hardware
execution action. Every returned report keeps all hardware/deployment/DDR flags
false. Explicit require_deployment always refuses, even if passed execute=true.

28 PIT unittest cases PASS. New hash tests mutate each of19 inputs independently
(10sources,6helpers,3artifacts), reject before structural checker invocation;
malformed profile/schema, extra execute field, missing closures and forged
hardware/deploy flags rejected. Fake files test hash-layer rejection only; actual
ELF structural PASS is separately recorded in audit.json. The existing guard
preflight rejects the new manifest schema before any hardware helper executes.
Existing hardware wrappers/manifests were not edited or repinned.

Hashes establish content consistency, NOT trusted provenance, reproducible
build, semantic correctness, exception/fault exclusion or permission to deploy.
A caller able to rewrite both bytes and hashes can produce a new audit input;
that still cannot obtain deployment from this gate. Direct ad-hoc tooling is
outside the gate: no software checker can prevent arbitrary user commands.
No new runtime hook, physical callbacks, mailbox or HW admission was added.

No JTAG/UART/network/reset/register access. Normal runtime unchanged. Physical
MMIO hang/fault recovery and PMU-to-AP0 publication visibility remain OPEN;
DDR NOT_ADMITTED. Next safe offline work: consolidate qualification gaps into
an image-specific adapter contract and review feasibility of bounded capture
without using timers as their own watchdog. Do not program this audit ELF.

Reproduce: python scripts/pit_audit_gate.py --manifest
 evidence/pit-source-artifact-gate-offline-2026-10-27/manifest.json
and python -m unittest discover -s tests -p 'test_pit*.py' -v.
