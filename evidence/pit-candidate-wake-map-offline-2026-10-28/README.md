# Candidate-specific interval event map — 2026-10-28

Read-only review of the exact 70-object rebuilt audit ELF; SHA-256 of ELF,
symbols and disassembly in review.json. Existing source-anchor and exception
inventory helpers were reused. No hardware command, event injection or policy
change. Existing profile/static gate and dated 64-test result remain unchanged.

Eight classes remain distinct: maskable interrupts; normal PM service; software/
hardware exceptions; external wake; debug; reset/POR; write-only sleep-fault
policy; terminal code. Linked PM service symbols and source anchors demonstrate
capability, not execution while the terminal loop sleeps or full LTO equivalence.
The audit entry still has no main/request hook. IE snapshots require honest,
returning callbacks and do not prove the whole publication-to-sleep interval.

RAM exception inventory reaches13 functions with148 memory operations and88
unresolved control entries. This overapproximation proves neither every edge
reachable nor every address unsafe; it prevents claiming exclusion from this
inventory. ROM/RAM forwarding remains physically unknown; GPO0 is write-only.
External Dont_Sleep writers, debug and resets are not excluded by a host lease.
No broad event masking or policy changes are justified to force qualification.

The three-word terminal loop is static evidence only. There is no proved
continuous no-wake lifetime, safe RAM consumer, or independent recovery from an
arbitrary stuck load. Next safe offline work is a consumer lifetime state-machine
contract that invalidates on wake/reset/debug/transport uncertainty and never
turns sampled status into RAM admission. No executor or hardware retry.
