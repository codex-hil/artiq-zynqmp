# Fresh GPO0-free terminal static-flow audit — offline

24 PIT tests PASS, including exact terminal ELF checker positive and eight
negative variants (barrier/sleep/branch/return/extra instruction, architecture,
entry and truncation). Actual standalone MicroBlaze v9.2 -Os linked ELF checker
PASS: three words b8220004 / ba020004 / b800fffc, mbar1 / sleep / branch to sleep.
No data access, call, return or escaping branch in the only code payload.
Function frame0; no undefined symbols. Explicit memory clobber in inline asm.
Compilation without the audit-only opt-in is rejected before producing object.

This is a newly generated independent terminal; no historical vector-v1 objects
or GPO0 reads are linked. The ELF uses entry/text address ZERO intentionally
for static analysis, NOT PMU RAM. Default linker also emits legacy RWE flags
and an uninitialized stack reservation; no stack operation is executed by the
three-instruction body. MUST NOT DEPLOY. It is not a bootable/full PMU firmware,
new guard profile, integrated capture path or independent recovery mechanism.

Source is deliberately audit-only. A real guard needs IRQ-state handling,
capture/publication before terminal entry, image-bound record/terminal addresses,
fresh lifecycle and artifact admission, and platform-qualified RAM/AP0 visibility.
A wake at the sleep instruction's following PC can only take the backward branch
in this static body; interrupt/exception/ROM/NMI/reset routes and actual sleep
residency remain outside this proof. No claim that mbar prevents a hung MMIO.
No hardware/JTAG/UART/network/reset/register access occurred. DDR NOT_ADMITTED.

Next safe offline work: link a fresh complete non-vector PMU audit profile with
collector/publication and this terminal (still no physical MMIO adapter), then
validate call ordering, record addresses, exception paths and fail-closed source/
artifact gates. No physical attempt follows from the standalone ELF.
Reproduce tests: python -m unittest discover -s tests -p 'test_pit*.py' -v.
