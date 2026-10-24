# Exact ELF printf table inventory — 2026-10-24

Offline only. Table0xffdd35d0 contains22 little-endian words for candidate
indices0..21 (format character minus99). All seven unique targets are aligned
inside xil_printf0xffdcc810..0xffdccbc0. This resolves the concrete table contents
behind bra r3 at0xffdcc9ec; it does not prove all paths use a bounded index.

Checker binds nine exact instruction words: bound constant21, subtract99,
unsigned compare, delayed conditional branch/shift, IMM/base addition, table
load and indirect jump. Conditional domination and MicroBlaze delay-slot control
semantics remain to be proven for all entries into this block. No external/ROM
target appears in these22 entries; no claim is made about corrupted/out-of-range
index, arbitrary memory writes, reset/NMI or other indirect control.

Two actual-ELF tests PASS, with controls for external/misaligned/end-of-function
targets, changed jump instruction and unmapped read. Initial instruction-negative
fixture FAIL is explained: searching for first occurrence of opcode bytes mutated
a different identical instruction. Fixture corrected to use ELF PT_LOAD address
translation; production checker already used address translation. No firmware or
hardware changed. DDR NOT_ADMITTED.

Next offline: establish branch domination/index bound using exact linked basic
blocks, then classify handler MMIO, formatting data and stack footprint. Keep
normal baseline and exception reporting unchanged; no repeated HW guard trial.
