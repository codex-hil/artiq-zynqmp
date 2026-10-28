# RO-context-v2 target branch/address/budget/state controls — offline

57 PIT tests PASS. New compiler-shape selector preserves forwarded-v1 historical
checks and adds ro-context-v2. Actual new ELF PASS:12direct calls/102entrybranches,
read_word14localbranches/two abstract read-call sites/one return, exact terminal,
entry+five forwarding no-subword checks. Entry prefix requires nonnull plan and
read adapter;30critical read_word instruction words bind armed/transport/busy/
failed/output checks, count<=7 encoding, modulo4/stride16/baseffd40044, address
comparison, consume-before-call, raw-error gate and staged output copy.

Nine consistent ELF+disassembly mutations rejected: WO preload alias, wrong bank,
ninth-read limit, wrong timer sequence, removed busy/failed guards, omitted count
consumption, ignored raw error, missing entry adapter-required branch. Both cross-
shape combinations reject. Prior ten control/symbol/disassembly negatives still
PASS. Synthetic ELF fixtures contain archived actual bodies, not bootable PMU
firmware. Initial new fixture used a wrong memset symbol offset, rejected as
expected; corrected from actual linked symbolffdd2760 before positive qualification.
No target ELF failure or hardware attempt was involved in that fixture correction.

Pins are intentionally compiler/ABI-shape-specific. No general symbolic dominance,
callback identity, timer units, fault preemption, complete memory semantics or
physical visibility proof. The host-model null-adapter fallback remains in
read_word; the new audit entry's adapter-required prefix is separately checked.
Hostile callbacks/state corruption remain outside the contract. No runtime hook,
physical MMIO wrapper, mailbox or deployment manifest was enabled. Old gate
continues selecting forwarded-v1; it was NOT extended to admit the new ELF.

No hardware/JTAG/UART/network/reset/register access. MUST NOT DEPLOY; DDR
NOT_ADMITTED. Next safe offline work: source/helper/artifact closure for this
specific new18-source RO profile, selecting ro-context-v2 explicitly and keeping
unconditional deployment refusal and prior profiles unchanged. Independent
hung-read recovery/AP0visibility/target hash provenance remain OPEN.
Reproduce: python -m unittest discover -s tests -p 'test_pit*.py' -v.
