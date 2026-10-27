# Fresh complete PMU audit link without historical vector guard — offline

Original vendor PMU sources rebuilt in a fresh isolated copy using the existing
boundary builder with lab_guard=false/vector_snapshot=false. Collector,
publisher, lifecycle model, new sleep terminal and new audit entry compiled from
current sources and linked with ONLY freshly rebuilt vendor objects. No older
vector-v1 application objects reused. Guard symbols absent. Vendor firmware may
legitimately access GPO0 elsewhere; this is NOT a claim of no vendor GPO0 access.
The new PIT components themselves contain no GPO0 diagnostic.

Final link and existing PMU footprint checker PASS, no undefined symbols. New
terminal ffdcf1a8 contains exactly mbar1/sleep/back-to-sleep; adapter ffdcf1b4
calls it. New entry ffdcf1c4/592bytes, LTO frame164; adapter frame4, terminal0.
Callback/caller/exception stack unknown; no total stack claim. Entry uses a local
ops copy, forces terminal_adapter and calls terminal again for rejected inputs.
There are no returns from the entry in the linked body. Abstract callbacks remain
indirect; no physical MSR/disable/read/write/barrier backend has been implemented.
Host model tests (24 PIT tests last PASS) do not execute this target wrapper.

This is a COMPLETE PMU ELF layout but NOT a working new capture profile. Entry
is retained with -u only; vendor main/request path has NO hook to call it.
No physical mailbox has been allocated/initialized or bound to its callbacks.
The previous BSS slot was a separate layout probe, not imported as an address.
Normal baseline runtime is unchanged. MUST NOT DEPLOY; no hardware action.

Next safe offline work: machine-check linked audit-entry branches/calls and
terminal bindings, with mutations for wrong terminal/return/escape, then define
source/ELF/symbol admission gates. Actual MMIO hang/fault recovery, session
freshness, PMU-to-AP0 visibility and physical restore qualification remain OPEN.
No device register/reset/UART/JTAG/network access. DDR NOT_ADMITTED.
