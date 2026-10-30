# Word-init MMIO bound audit gate — offline, 2026-10-30

New explicit profile pit-mmio-word-init-bound-audit-v1 has an exact20custom
source/header closure, seven helper scripts and three artifact pins. Hashes are
verified before layout/flow checks, and the same artifact bytes are hashed and
checked. Eight project-function bodies (648words) are exact range/SHA-pinned and
checked for no subword stores. This is scoped consistency, not generic control-
flow/dataflow proof or global vendor-library/callback/exception qualification.

89 PIT tests PASS:30file-change controls reject before structural analysis;
19labeled and648individual-word mutations reject; missing closure/claim/schema/
CLI --execute controls reject; require_deployment always refuses. Actual current
ELF passes. Both image revisions reject the wrong pin checker; old generic/RO
bound gates and new gate reject crossed profile manifests (six actual controls).
The old libraries/image with byte-path memset evidence remain unchanged.

No hardware access, physical image/plan hook, mailbox ownership, continuous sleep
or independent recovery proof. Decoder returnfalse for external_callback_paths_
qualified prevents promoting scoped width to all paths. Old working-source
manifests remain stale after the intentional pit_capture fix; don't repin them.

Next safe offline step: freeze the new20+7+3closure in isolated local copies and
replay after relocation with independent inventory anchor and tamper controls.
Do not replace older frozen snapshots or treat exact hashes as build provenance.
