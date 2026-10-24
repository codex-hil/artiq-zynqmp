# Exception format, arguments and frame inventory — 2026-10-24

Read-only offline extraction from exact sleep-guard ELF. No HW access.
Format0xffdd2314 is a local NUL-terminated65-byte string (including NUL), with
four %x fields and no %s, pointer-dereference or dynamic-width directive.
Handler loads MSR/EAR/EDR/ESR directly into r6/r7/r8/r9 before xil_printf.
Those values are integer formatting inputs, not string addresses.

Printf spills r5..r10 at caller-SP+4..24, then allocates104bytes. Its varargs
cursor is new-SP+112 = caller-SP+8, corresponding to r6. Four32-bit arguments
occupy caller-SP+8..20. Handler has a28-byte frame, so these spills fit inside
that frame when entered through the ordinary linked call sequence. This is a
local ABI observation, not proof of arbitrary/nested exception entry SP.

ELF _ctype_ is257bytes at0xffdd3874. Linked byte classification uses base+1
and byte-derived index. Complete helper register/dataflow/format-only path pruning
remains unproven. Format and table contents are local PMU data, not DDR.

Six functions have negative SP adjustments: handler28, printf104, outnum108,
padding12, udiv12, umod12. Their static sum276 is NOT a runtime stack bound.
Linker stack is0xffddc55c..0xffddd560 (4100bytes). Existing PMU caller frames,
entry SP, interrupted execution, repeated allocation, nesting/error/reset paths
and write corruption must be accounted for before comparing usage to capacity.
The current guard itself retains its28-byte frame and prior call frames too.

Next source/linked audit: ordinary XPfw_CoreLoop->telemetry->guard call-chain
stack at exception entry and architectural hardware exception nesting/entry
behavior. Preserve exception reporting; do not obtain a convenient bound by
clearing EE. No unchanged HW capture. DDR remains NOT_ADMITTED.
