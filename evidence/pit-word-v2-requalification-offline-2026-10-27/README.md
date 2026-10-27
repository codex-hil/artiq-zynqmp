# Word-v2 linked-flow and alignment requalification — offline

31 PIT tests PASS. Flow checker has distinct legacy-v1 (historical) and word-v2
shapes; cross-shape fixtures rejected. New actual ELF word-v2 passes 27 internal
branches, nine abstract callback sites, exact terminal/adapter, one memset and
no subword store opcode. New manifest binds10current sources/7helpers/3artifacts;
actual combined layout/flow/word-store audit PASS. Profile identifier changed to
pit-counter-before-sleep-word-audit-v2. No old manifest or raw proof rewritten.
Both shapes remain NOT_DEPLOYABLE; explicit deployment refusal unchanged.

New compiler inventory: read callback r28, writes r25, barriers r26; initial
MSR r22 and disable r29. One memset replaces the old two-call inventory after
explicit volatile u32 staging initialization. Historical scoped checker tests
retain original function bodies; v2 fixture uses archived new body, all synthetic
ELF fixture bytes are labeled as such. Current real audit uses actual linked ELF.

Conditional alignment review: entry SP must be word-aligned under the ABI.
Frame164 and record offset28 preserve word alignment (-164+28=-136). The single
memset length48 starts aligned and follows the reviewed library word path:
three16-byte groups, no prefix byte alignment or remainder stores. This is a
static path review with alignment/input assumptions, not target execution or
proof of every library/exception path. Saved registers and fixed stack word
stores use multiples of4; indexed staging addresses are built with shift-left2.
Abstract callbacks still require their own access/alignment/recovery review.
No MMIO backend/runtime hook/mailbox/session or visibility qualification added.

No HW/JTAG/UART/network/reset/register access. MUST NOT DEPLOY, DDR NOT_ADMITTED.
Next safe offline work: inspect callback error/terminal entry context and remaining
stack/init paths for a minimal physical adapter proposal, keeping independent
hung-read recovery and PMU-to-AP0 visibility as unresolved requirements. Do not
interpret these static passes as permission for a new hardware attempt.
Reproduce: python scripts/pit_audit_gate.py --manifest
 evidence/pit-word-v2-requalification-offline-2026-10-27/manifest.json
and python -m unittest discover -s tests -p 'test_pit*.py' -v.
