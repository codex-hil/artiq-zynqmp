# RO-context bound audit gate — 2026-10-28

Offline only. The actual RO-context ELF passes the separate v2 gate with exact
18-source/header, seven-helper and three-artifact SHA-256 closure. The checker
explicitly selects ro-context-v2. The old forwarded-v1 gate is unchanged.

60 PIT tests pass. Controls change each of 28 pinned inputs before structural
checks, reject missing closure members/extra fields/claim flags, reject crossing
profiles, verify explicit shape selection and unconditional deployment refusal;
the CLI rejects --execute and the existing hardware preflight rejects this profile.
The real-artifact positive result is check.json; manifest.json pins the local ELF
and companion files (not distributed here). Paths require those local artifacts.

This establishes content consistency and static structure, not trusted build
provenance, a physical backend, bounded MMIO, AP0 visibility or execution of sleep.
No hardware access, target programming or DDR admission occurred. An intermediate
implementation used an incorrect keyword for the checker; it was corrected to
its actual shape parameter before the real-artifact audit and final suite.

Next safe step: freeze and replay this v2 source/helper/artifact closure in an
isolated relocated snapshot with independent tamper controls. Do not repin or
replace the historical forwarded-v1 snapshot.
