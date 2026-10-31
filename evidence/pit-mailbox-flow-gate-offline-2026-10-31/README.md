# Owned mailbox instruction and source audit

LGPL-3.0-or-later. Offline only; no hardware operations.

The actual mailbox-binding ELF passed the separate instruction/storage checker and source-bound gate. The manifest pins 27 C/header inputs, eight helpers and three local artifacts. The full vendor-containing ELF remains local at the manifest path. This is content consistency, not authenticated provenance or reproducible-build proof.

104 Python tests passed, including 19 labeled instruction mutations, mutation of each of 911 scoped instruction words, storage/listing rejection and 38 pinned-file tamper controls. The 16 exact function bodies bind this specific reviewed build; this is not a generic CFG/dataflow proof. External callback paths, exception behavior and total stack remain unqualified.

Deployment is always refused. No PMU request hook, qualified MSR/disable callbacks, digest producer, external RAM reader lifetime or arbitrary-hang recovery is established. Existing physical results are unchanged. Next: freeze and relocate this exact closure and verify independent replay and rejection controls, without hardware access.
