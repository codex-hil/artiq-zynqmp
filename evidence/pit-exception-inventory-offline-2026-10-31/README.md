# Static vector/exception dependencies — offline 2026-10-31

LGPL-3.0-or-later. Read-only artifact/source review, no hardware operation,
physical fault injection, vector change or runtime/frozen image modification.

Four ELF vectors decode to XPfw_Init (reset), XPfw_Exception (software exception),
XPfw_InterruptHandler/_interrupt_handler (IRQ), and XPfw_Exception_Handler (hardware
exception). Decode verifies unique file-backed raw instruction bytes and branch
targets. This is ELF content, not observed vector selection or live routing. NMI,
ROM/debug/error routes are not excluded by missing ELF vector names.

IRQ entry allocates80 bytes, saves/restores registers/MSR, dispatches via22-entry
mask/handler table at ffdd4980, acknowledges MMIO and returns with rtid. Table
entries are recorded, not transitively stack/behavior qualified. Pending/level
sources, repeated/nested dispatch and all handlers remain outside normal-path
stack bound. Clearing IE on one normal path does not establish their exclusion.

Software exception path (60 bytes/no explicit frame allocation) writes ESR/EAR
to ffd80050/54 and error bit to ffd6033c, then loops. It is not successful PIT
terminal/sleep or generic recovery. Hardware exception handler (116 bytes/frame28)
reads special registers, calls xil_printf and XPfw_UtilRMW then loops. Source
xpfw_core.c:501 confirms error notification plus nonreturn; no automatic recovery.
No reset behavior is inferred from firmware error notification alone.

Concrete hardware-admission gap: actual linked xil_printf (944 bytes/frame104)
has stack byte stores at ffdcd718 and ffdcd790. Existing word-store checker rejects
it at ffdcd718, as expected. Thus previous normal-path scoped word-store PASS
cannot qualify the exception route. Its UART/output/format helpers and variadic
argument homes add dependencies not covered by the792-byte model. Frame28+104
is only a local nested subtotal, not a bound on interrupted/nested exception stack.
No need to execute an exception to establish these static out-of-scope byte stores.

Existing137-test normal-path suite is unchanged and not rerun; this turn adds
reproducible static inventory, exact input/source hashes, archived disassembly and
an actual negative word-store check. Expected rejection is an inventory finding,
not hardware failure or a waiver of PMU RAM word-store requirements.

Next safe offline step: design a separate audit-only word-oriented fail-stop
exception receipt with no printf/UART or returning recovery claim, including safe
special-register capture, owned storage and preservation of normal firmware/vector
policy. Review exact entry/stack assumptions and schema before implementation or
new links. Do not disable exceptions or replace production vectors as a shortcut.
Entry authorization/image trust/no-wake reader lifetime/arbitrary-hang recovery
remain open; no deployment or external PMU RAM consumer admission.
