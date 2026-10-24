# Printf range and direct exception MMIO review — 2026-10-24

No HW access. Exact ELF/table and delay-aware structural checks rerun PASS.
AMD UG984 instruction summary specifies CMPU sign from unsigned rB<rA:
https://docs.amd.com/r/2024.1-English/ug984-vivado-microblaze-ref/Instruction-Summary
Delayed BLT branches on negative result and executes its slot before transfer:
https://docs.amd.com/api/khub/documents/nFSf4DzHSH69wDPCjkWCXA/content

At0xffdcc998 taken branch targets0xffdcc9d0; its delay slot0xffdcc99c sets r4=21.
The linked table does not target the index block, and no other annotated direct
branch targets its interior. At d0 r3=(character-99)mod2^32; d4 CMPU r18,r3,r4
sets sign iff unsigned index>21. At d8 BLTID sends rejected values to0xffdcc9c8.
Its shift delay slot executes for both outcomes, but rejected values never reach
the table load through this edge. Surviving index0..21 produces offsets0..84,
so the4-byte load stays within table0xffdd35d0..0xffdd3628. Ten arithmetic
boundary controls include negative-wrap/high-bit cases; these are software models,
not PMU execution. All statements remain conditional on CFG/callee assumptions.

Direct linked memory review:
- Software exception stores ESR/EAR at0xffd80050/54 and FW error at0xffd6033c.
- Hardware exception invokes XPfw_UtilRMW at0xffdc5b60 with immediate addresses
  0xffd80064 and0xffd6033c. Helper performs one load and one store through r5;
  it has no nested call and returns through r15. Error side effects not excluded.
- outbyte0xffdcbb38 polls0xff00002c and writes one masked byte to0xff000030.
  Busy polling has no finite execution bound if UART remains full.

These explicit addresses are not DDR. This does not classify all148 inventoried
memory operations: printf format/ctype/string/varargs, stack, helpers and potential
nonlocal/reset/ROM behavior remain open. Do not infer complete no-DDR footprint
or forward progress from this partial classification. Preserve reporting and ACK0.
DDR NOT_ADMITTED; normal baseline untouched, no fresh health check.

Next offline: bind exact format string/ctype/varargs ranges and exception stack
budget, starting from actual handler arguments and linker stack symbols. Avoid
additional successful guard captures or arbitrary interrupt masking.
