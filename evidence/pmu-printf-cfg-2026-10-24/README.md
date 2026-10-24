# Printf structural dominance — 2026-10-24

Offline exact-image audit. Every instruction word in the printf interval is
compared against ELF PT_LOAD bytes. Context nodes distinguish delay-slot execution
from ordinary entry, with conditional outcomes overapproximated. The seven known
indirect table destinations are all included. Calls are assumed to return to their
own continuation and preserve ABI; this is an explicit unproved boundary.

The bound constant21, subtract99, unsigned comparison/branch, shift, table-base
construction and load structurally dominate bra r3. Removing any required node
makes the indirect jump unreachable in this model. Two tests PASS: actual graph,
synthetic bypass rejection, ELF/text mismatch rejection and incomplete graph
rejection. Early prototype rejected bslli as a branch in a delay slot; corrected
opcode classification and actual audit then passed. First cfg.json is structural
prototype output; verified-cfg.json additionally checked all instruction bytes.

AMD UG984 documents delayed conditional branches executing the next instruction:
https://docs.amd.com/r/2025.2-English/ug984-vivado-microblaze-ref/bgti

This is structural dominance, not proof of register ranges or exception exclusion.
Next resolve CMPU/BLTID value semantics and verify reaching definitions of r3/r4
on the guarded path, then helper ABI and memory footprint. No HW access, exception
masking or firmware changes. DDR remains NOT_ADMITTED.
