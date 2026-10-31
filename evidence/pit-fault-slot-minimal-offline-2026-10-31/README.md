# Minimal digest/fault-slot audit link — offline 2026-10-31

LGPL-3.0-or-later. No hardware operation or runtime/vector change.

Separate fresh19-custom-C-unit LTO build excludes six old parallel audit profiles:
pit_capture, pit_sleep_model, pit_status_compose, pit_mmio_composition_audit,
pit_mailbox_composition_audit and pit_irq_composition_audit. New digest lifecycle/
composition/root remains present. Original failed25-unit build/log unchanged.
Vendor objects/BSP archives reused; no undefined symbols. No source implementation
changed this turn; existing143-test result remains dated and was not rerun.

Link now PASS with original linker script/stack/service-table constraints:
_stack_end ffddddec, _stack ffddedf0, symbolic range4100 bytes (same as old image).
Fixed service table begins ffddf6e0,2288 bytes above stack top. No stack shrink,
table movement, relaxed assertion or removal of normal vendor code to gain room.
The linker script current hash and exact custom source delta are recorded.

Owned fault slot ffddd400/64 bytes/8-byte alignment is unique zero-BSS, disjoint
from owned sample/terminal mailbox and before stack. Raw file-backed/BSS mapping
checks pass. Formatter is inlined into fault writer ffdd078c/440 bytes/frame132;
no direct/indirect calls remain, two mbar1 at ffdd08d4/ffdd0904, scoped word-store
checker PASS. Digest root ffdcfdd4/2488 bytes/frame332; ordered reader frame44.
ELF layout and normal mailbox checks PASS. New LTO layout is distinct; old exact
profiles/792-byte graph are NOT applied to changed code or addresses.

Retained fault writer is still not called by an exception vector or normal main.
It accepts supplied words/C stack and returns; it is not a fail-stop entry stub,
reentrancy protection, special-register capture or physical visibility proof.
Existing exception printf route remains in vendor firmware and unqualified.

Next safe offline step: exact instruction/storage/fence profile for the inlined
fault writer in this minimal ELF, with word mutations and slot/state/stack/table
boundary checks. Preserve old artifacts and failed link; no physical exception
injection, vector replacement, external RAM read or deployment is admitted.
Actual exception entry/stack/reentrancy/notification/sleep/recovery remain open.
