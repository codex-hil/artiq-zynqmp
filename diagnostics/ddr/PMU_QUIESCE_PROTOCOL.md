# PMU diagnostic quiescence — proposed, not deployed

Current checkpoint: explicit sleep/reentry guard was physically captured with
ACK0 on2026-10-23; normal runtime restored. Earlier proposed/unselected/nop-loop
statements below describe historical stages. See [current admission status](ADMISSION_STATUS.md)
and the2026-10-24 post-guard review; no full DDR admission exists.


The existing AMD PMU services must remain functional during trained FSBL boot.
A reduced firmware is not an approved replacement. The model in
`pmu_quiesce_model.py` describes transition rules only; its receipts are explicitly
marked offline and are NEVER DDR write permits.

Proposed sequence:

1. CPU0 has completed trained FSBL handoff and is stopped at the checked OCM
   observer terminal. The no-master PL image and existing necessary master
   observations have been verified under the shared lease.
2. An explicitly registered diagnostic AMD PMU module receives a request through
   a reviewed transport. It records boot epoch and nonzero sequence, but does
   **not** acknowledge quiescence from an IPI/interrupt handler.
3. After the handler returns, a diagnostic hook at the `XPfw_CoreLoop` boundary,
   before sleep or scheduler processing, may examine the request. Existing source
   shows the scheduler/sleep boundary; no hook has been installed. A wake/request
   mechanism must bring sleeping PMU to this boundary without invoking unintended
   service callbacks. An interrupt-handler return alone is not this proof.
4. The hook may publish acknowledgment only after verified exclusion of active
   handlers, scheduler execution, interrupt delivery, other-core reset release
   and PMU memory access, plus a separately established transaction-history/drain
   condition. Those are obligations requiring implementation and source/hardware
   evidence, not trusted booleans written by the host. PMU interrupt disable alone
   does not exclude ROM/NMI/error paths. Any unresolved obligation rejects admission.
5. After acknowledgment PMU stays in a reviewed instruction/memory footprint
   outside tested DDR. A heartbeat or mailbox read must not introduce DDR access.
   Acknowledgment must be committed last after barriers and read back coherently;
   the final hardware gate will bind image, entry state and that same boot epoch.
6. A host deadline before acknowledgment rejects the request; DDR never starts.
   A deadline, host disconnect, or malformed request after acknowledgment NEVER
   automatically resumes PMU. There is no resume command. Restore by the existing
   full PS reset → AMD PMU/FSBL → normal runtime lifecycle, even after failures.

The transport is **UNSELECTED**. Do not reuse failed AP0 private PMU reads or invent
an alias. A prospective OCM mailbox must first be checked against ALL FSBL/model
ELF memory extents, stack, debugger downloads and BSS zeroing. In particular the
model's RW PT_LOAD spans `0xfffc8cf0..0xfffe4000`, including a linker gap; putting a
mailbox in that gap would let a download clear it. PMU-private RAM/debug-target
access also needs a proven, non-disruptive observation route. No MMIO address or
IPI command number is allocated by this design.

The seven-condition model exhaustively tests all 128 combinations, stale epoch/
sequence rejection, malformed fields/clock rollback, and pre/post-ACK deadlines.
These tests validate protocol rules, not that the obligations can yet be met.
Next implement source-only hook/module/transport integration in an isolated AMD
source copy, preserving the current firmware and normal boot services. Do not load
it before memory footprint, ROM/NMI/error exclusions and restoration are reviewed.


2026-10-23 IRQ-mask policy review: direct maintained
`microblaze_disable_interrupts()` clears IE0x2, while exception-disable clears
EE0x100 and Xil_ExceptionDisable may call both. Keep hardware exception reporting
available in a proposed laboratory guard; do not use broad exception-disable as
quiescence proof. Compile/disassembly evidence is in pmu-irq-policy-2026-10-23.
A default-disabled guard could enter an instruction-only PMU-local loop after
IE readback, without scheduler/resume/DDR callbacks; this has not been built or
run. It would still carry ACK0 with ROM/NMI/error/history/core exclusions unresolved.
