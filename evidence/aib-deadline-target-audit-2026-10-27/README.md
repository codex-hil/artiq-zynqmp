# Post-deadline-fix MicroBlaze ABI/LTO audit — 2026-10-27

Offline only. ActualPMU compiler/link recipe rebuilt strict/session/backend after
write callback ABI change. Isolated AUDIT_ONLY ELF/local footprint check PASS.
No ordinary main/guard call, real MMIO transport, device access or deployment.
Compiler pipe/serialLTRANS warnings retained; no compile/link error.

Exact native call-site words identify write callback from io+8; r5context,
r6request,r7/r8start,r9/r10timeout. Callee preserves start into r24/r25 and timeout
into r23/r22 across timer/recheck calls. abi-check.json pins eleven instruction
words and ELF hash. This is a register assignment inventory, not independent
whole-path dataflow proof or actual target execution.

Host actual C optimized+ASan/UBSan deadline fixtures PASS across three clock
variants: zero base, high64bit base and timeout/delay exceeding2^32. Six scenarios
per variant: normal ACK, delayed recheck preventing dispatch, submitted write
finishing late without rollback, backward clock, clock failure and arbitrary
transport error not masquerading as cancellation. Prior source state preserved
in earlier evidence; no old target checker is silently requalified for new ELF.

Current finalLTO frames: execute172,snapshot48,read28,write76,ticks28,prepare56,
arm0bytes. Write frame rose44->76. Internal read path172+48+28=248 and write
path172+76=248, both exclude caller/transport/library. Neither is full stack bound.
All callback/timer hardware mapping, bounded bus completion and competing-writer/
source-core/ROM access exclusions remain open. Do not admit writes from size alone.

Next safe offline work: specify real timer units, wrap/rollback policy and bounded
register-transport fault behavior, including acceptance-uncertain write handling.
A software deadline cannot preempt a hung MMIO transaction. Review platform timeout
facilities before a physical backend is chosen. DDR remains NOT_ADMITTED; normal
runtime untouched, no unchanged HW retry.
