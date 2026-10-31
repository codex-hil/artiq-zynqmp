# Concrete digest audit root — offline 2026-10-31

LGPL-3.0-or-later. No hardware operations, no deployment/runtime entry hook.

New root requires explicit target/terminal/MMIO/IRQ audit opt-ins. It rejects
consumed/nonzero plan/results, preselected callbacks, non-NULL contexts, absent
nonce/image or all-zero image before preparing. A separate zero-BSS ordered-read
adapter is prepared with raw PIT callback/NULL context, then owned mailbox slots
are prepared. Partial preparation failure enters terminal; no retry/rearm. Root
binds IRQ observers/disable, ordered read wrapper, sample/receipt writers/fences,
runs new digest composition, then enters existing nonreturn terminal audit loop.

Host explicit doubles check13 guard/preparation/binding/transfer cases under O2
and ASan/UBSan. The wrapper rejects non-NULL read context, passes actual adapter to
read function, and composition receives exact expected callback pointers. These
doubles do not prove physical behavior. Existing ordered-read unit tests exercise
actual adapter; root test deliberately doubles it to isolate binding/early refusal.
Full126-test Python suite PASS.

Fresh24-custom-C-unit small LTO ELF PASS with reused vendor objects/BSP archives,
no undefined symbols. LTO inlines digest lifecycle/terminal/compose into root:
ffdd0b9c/1500 bytes, frame336. Ordered read wrapper frame28; capture156 and SHA300.
Root+capture+SHA path scoped subtotal792, not full caller/callback/exception stack.
Private adapter at ffdddbb8/24B.29 scoped word-store checks plus ELF/mailbox layout
PASS; linked disassembly archived. Root direct-call targets recorded separately;
indirect callback and complete CFG/liveness/exception proof are not supplied.
Earlier root/profile images remain unchanged and old exact gates are not repinned.

The linked image retains old IRQ audit root as well for separation; normal firmware
main does NOT call the new root. A retained root in ELF is not hardware deployment
or entry qualification. External image digest remains untrusted caller input; no
loader protocol is present. Terminal loop intent still cannot prove no-wake sleep
or permit external PMU RAM reads. Arbitrary hung MMIO recovery remains unresolved.

Next safe offline step: distinct exact instruction/storage/constants/source-bound
gate for this actual artifact, with binding/failure/ordered-read/SHA constant and
per-word mutation controls. Do not apply prior exact profiles to new addresses or
claim whole stack/exception/physical ownership. No HW admission follows.
