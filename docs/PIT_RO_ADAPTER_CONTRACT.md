# PMU-local RO PIT adapter contract — 2026-10-28

**Offline component only. Physical backend NOT_READY; no hardware attempt selected.**
[Evidence](../evidence/pit-ro-adapter-contract-offline-2026-10-28/README.md).
This narrows a future counter diagnostic, not destructive DDR admission.

| Aspect | Contract |
|---|---|
| Allowed reads | PIT0..3_COUNTER at ffd40044/54/64/74, in that order, twice |
| Maximum raw callback invocations | Eight; consumed before each invocation |
| Wrong address/order, null output, extra read | Reject before transport; attempt cannot resume |
| Nested entry | Reject before transport; not a thread lock |
| Raw return zero | One word returned; staged result copied to caller |
| Raw return nonzero | Ignore output, latch failure, no retry or re-arm |
| Wall-clock deadline | None; callback can hang or trap |
| Device-register write API | None; underlying transport must honor read-only contract |

Caller owns zero-initialized state in one execution context. It must not reset,
reuse or mutate state to create a second attempt. Session/image binding and board
lease are external requirements, not properties of this small adapter.
A malicious callback can lie or write hardware; the type signature is no sandbox.

A concrete MicroBlaze Xil_In32 wrapper is **not implemented**. BSP Xil_In32 has
no bus-error result; return0 after a load must never be described as successful
fault handling. Software timeout cannot preempt that load. IRQ/ROM/exception
behavior, trusted callback implementation and independent recovery remain open.

After local capture, sample and terminal-intent publication still require
32-bit aligned word writes, image-bound mailbox ownership, ordering and actual
sleep/AP0 qualification. No pre-sleep record proves sleep. Old fixed-address Tcl
helpers and write-only GPO0 reads remain prohibited shortcuts. No timer control,
preload, prescale, watchdog, reset or ATB changes are authorized by this contract.

Before any later HW access, owning-station identification and shared Genesys
lease must cover every reset/JTAG/UART/AP0/network/test/restoration step. The new
profile remains disabled; [qualification checkpoint](PIT_QUALIFICATION_CHECKPOINT.md)
continues to separate offline PASS from missing physical evidence.

## Returning composition qualification — 2026-10-28

55 PIT tests PASS, including11actual C fake-backend composition cases; all read/
address/budget failures produce READ_FAILED with zero sample writes. Receipt
bytes crosschecked by Python. This is host fixture wiring, not target profile
integration or physical qualification. [Evidence](../evidence/pit-ro-composition-offline-2026-10-28/README.md).
