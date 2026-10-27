# Scoped full-profile linked flow controls — offline

Actual fresh PMU audit ELF check PASS: exact terminal/adapter, 24 branches stay
inside entry, direct calls resolve to terminal_adapter, memset twice and final
terminal, nine reviewed indirect callback sites/registers. Function instructions
are compared against ELF payload bytes rather than trusting disassembly alone.
No historical guard symbols allowed, no return or unreviewed instruction allowed.
Entry ends at a direct terminal call plus its delay slot, not fallthrough.

26 PIT tests PASS. New controls reconstruct a SYNTHETIC minimal ELF from the
archived real function bodies and mutate both ELF and disassembly consistently:
missing terminal barrier, adapter wrong target, entry wrong direct target,
return instruction, escaping conditional branch, unreviewed callback register;
seventh control changes ELF only and rejects stale disassembly. These are
static mutation tests, not newly compiled firmware or target execution.

Checker is intentionally compiler-shape-specific and scoped, not a complete
MicroBlaze decoder, symbolic execution, CFG liveness or dataflow proof. Local
branches remaining inside the function do not prove MSR-check dominance or
termination; abstract callbacks can hang, trap or behave incorrectly. Register
inventory is not callback identity/authentication proof. memset semantics and
ROM/exception/reset routes require separate review. No hardware-admission claim.
No physical backend/mailbox/runtime hook was added. Audit ELF MUST NOT DEPLOY.

Next safe offline work: source/artifact-bound gate which refuses this audit-only
profile and any changed symbol/ELF/helper pins before physical tooling. Keep
freshness, access/fault recovery, AP0 visibility and full restore obligations
explicit; none can be waived by static flow PASS. No HW/network/UART/JTAG/reset
access occurred; DDR NOT_ADMITTED.
Reproduce: python -m unittest discover -s tests -p 'test_pit*.py' -v.
