# Concrete RO counter adapter contract — offline

54 PIT tests PASS. New callback adapter admits exactly eight ordered PMU-local
counter addresses, consumes each attempt before raw transport, rejects reentry,
invalid/WO/unreviewed/out-of-order/unaligned addresses before any transport call,
and latches failures/no retry. Failed transport output is staged locally and
never copied to caller. Extra ninth read/reprepare rejected. Actual collector
integration and all eight transport-error positions tested optimized+ASan/UBSan.

MicroBlaze standalone non-LTO link PASS/no undefined symbols; prepare/read scoped
word-store checks PASS, frames0/44 exclude raw transport/caller. Text at zero,
MUST NOT DEPLOY. There is NO actual MMIO backend or profile integration. Address
constants match the pinned installed AMD pmu_iomodule.h counter macros; register
access qualification remains the prior UG1087 review, not header names alone.

No elapsed-time bound is claimed. Xil_In32 is a volatile load without error return:
a future wrapper returning0 means only that the instruction returned a word.
A fault can trap or hang and cannot become this adapter's nonzero callback result.
Fake transport errors test software behavior only. No arbitrary aliases, reset/
watchdog/ATB policy writes, GPO0/preload/control reads or timer reconfiguration.
Underlying transport must itself be trustworthy/read-only; this adapter cannot
prevent hostile callback side effects and is not a lock/security boundary.

No HW/JTAG/UART/network/reset/register access. New component not added to current
audit image/gate. Existing frozen snapshot remains historical/unchanged. DDR
NOT_ADMITTED. Next safe offline work: integrate this sequence-limited transport
wrapper into the returning composition model with fake callbacks, checking that
address/budget failure cannot reach sample/status success before target re-link.
See docs/PIT_RO_ADAPTER_CONTRACT.md. Independent recovery/AP0 visibility OPEN.
