# Synthetic non-PMU entry link — offline 2026-11-01

LGPL-3.0-or-later. Static relocation fixture only, never hardware firmware.
No board access, vector replacement, live fault, runtime or frozen-image change.

Only original standalone assembly object is linked (--no-relax) with explicit
bounded synthetic map: CODE0x10000/256B read-execute, SLOT0x20000/64B read-write
zero-BSS. Link script asserts exact code/slot sizes and zero vector/stack/heap
sections. These addresses are intentionally not the PMU runtime map. ELF entry
is the software candidate at0x10000 for link metadata only; never executed.

Both entry functions retain32 words/128 bytes; slot address relocation resolves
to IMM2/addik r8,0,0 pair, exact64B/aligned8 BSS. No remaining relocation sections,
vector/call/stack/SDA dependency; two mbar1 per route and final local self-loop
remain exact. Checker validates raw code, ELF load map, symbols/sections/listing.
64 word mutations, changed map/symbol/listing controls reject. Existing actual
PMU boundary checker rejects the fixture, preventing confusion with full firmware.

This does not establish linked PMU slot ownership, startup/BSS execution, special
register privilege, nested/repeated-entry exclusion, notification preservation,
external memory visibility, sleep or recovery. Multiple entries share a slot;
partial/nested publication remains explicitly unqualified. Production printf
exception path is still unchanged/unqualified. No deployment/PMU RAM reader permit.

Next safe offline step: model partial and nested entry store sequences against
strict fault-record decoder, identify torn/overwritten/commit interleavings and
state precisely what single-writer assumptions are needed. A model cannot justify
physical exclusion or recovery; do not add a reentry flag or change exception
policy as a shortcut. Keep synthetic fixture separate from runtime artifacts.

Full PIT Python suite:152 tests PASS.
