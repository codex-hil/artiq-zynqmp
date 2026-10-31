# Linked IRQ binding audit — 2026-10-31

LGPL-3.0-or-later. Offline small C/LTO rebuild; no hardware operation.

New root pit_irq_composition_audit rejects invalid/consumed plans and preselected
MSR/disable callbacks before mutation, binds the two concrete audit callbacks,
and delegates to the existing owned-mailbox root. No main/request hook added.
17 custom C units compiled fresh; vendor objects/BSP archives reused. No undefined
symbols. Host transfer doubles pass 13 guard/binding cases plus NULL plan under
optimized and ASan/UBSan builds. All 106 Python tests pass.

Actual linked instruction review: root ffdd0078/224 bytes/frame28 stores MSR
callback ffdcc244 at plan+116 and disable ffdcd038 at+120, then calls mailbox
root ffdcfe98 (delay-slot store included). MSR callback 60 bytes/frame0 has one
mfs rmsr and one swi output, with context/alignment/NULL guards. Disable callback
56 bytes/frame8 has one call to ffdcd008. Layout, mailbox and five scoped
word-store checks pass. Compiler ordering is not bus fencing.

Critical difference from standalone evidence: linked microblaze_disable_interrupts
is the 48-byte C helper from BSP xil_exception.c, not the five-instruction .S
helper. It loads the configuration flag at ffdd8b94 and selects msrclr r0,2
or mfs/andi -3/mts. Both instruction paths clear IE mask2; actual live selection
is NOT observed. The read-modify-write path is not atomic against exceptions.
No direct hardware MSR/IRQ proof or all-exception exclusion follows. Archived
linked disassembly, not earlier standalone helper evidence, applies here.

Root+mailbox+MMIO root+disable forwarder+IRQ callback frame subtotal is
28+28+296+28+8 = 388 bytes, helper frame0. This is a scoped subtotal only,
not whole stack/exception proof. New addresses invalidate old exact pins by
design. Old frozen profiles and their claims remain unchanged. Digest origins,
request hook, exception/error paths, reader no-wake lifetime and arbitrary-hang
recovery remain unresolved; deployment and external RAM reading remain refused.

Next safe offline step: separate exact instruction/storage and source-bound
profile for this actual linked image, including BOTH helper paths/configuration
read and callback bindings; mutation controls must reject changed paths/targets.
Do not reuse old mailbox or standalone helper qualification as a new-image gate.
