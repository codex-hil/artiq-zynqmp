# Ordinary guard stack entry and hardware exception review — 2026-10-24

Offline exact ELF check. XPfw_Init initializes r1 to0xffddd560, then calls
XPfw_Main at0xffdc00ac. Main allocates64bytes at0xffdc8ad8 and directly calls
guard at0xffdc91cc. Guard allocates28bytes at0xffdc4660 and never returns.
CoreLoop/telemetry were inlined: do not invent extra frames from source names.
Assuming ordinary balanced prior calls, retained frames total92bytes and r1 at
terminal is0xffddd504. No live SP was captured in the previous physical trial.
Four exact instruction words were checked against file-backed ELF mappings.

Adding prior conservative exception-function frame inventory276 yields368bytes
and0xffddd3f0, still within linker stack0xffddc55c..0xffddd560. This arithmetic
is NOT an established runtime bound: all helper paths, frame reuse/allocation,
entry correctness, reset/break/ROM behavior and data corruption need accounting.
Configured XPAR_PSU_PMU_USE_STACK_PROTECTION=1 is source configuration, not proof
that every memory access is protected (particularly accesses not based on r1).

AMD UG984 exception entry sets EIP and clears EE; a nested fault can halt for
certain configured fault-tolerant cases. Actual PMU C_FAULT_TOLERANT was not
established from the inspected BSP header; do not infer it or recursive safety.
Handler does not execute RTED on its ordinary path, so it does not normally
restore EE. Reset and non-maskable break remain separate higher-priority paths.
Sources:
https://docs.amd.com/api/khub/documents/rTUOTl4uJGQpo~srDWVjRg/content
https://docs.amd.com/r/en-US/ug984-vivado-microblaze-ref/Reset-Interrupts-Exceptions-and-Break?contentId=ivWxu~Xc7KeYSjvApn9jDw

Next offline boundary: inspect linked break-vector bytes and actual PMU core
configuration/ROM handoff before selecting further exclusion instrumentation.
Do not mask exceptions, force debug reads or repeat the successful guard trial.
DDR NOT_ADMITTED. Normal runtime unchanged; no new hardware health check.
