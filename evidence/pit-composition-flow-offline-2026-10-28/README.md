# Forwarded composition linked-flow controls — offline

2026-10-28:51PITtestsPASS. Actual new PMU audit ELF check PASS: entry12direct
calls resolve to observe3/disable1/read1/write3/barrier2/memset1/terminal1;
entry5indirect receipt calls use reviewed register inventory;97entry branches
stay within its function and entry cannot return. All five forwarding functions
have one abstract indirect callback and one expected return; their branches stay
local. Terminal remains exact mbar1/sleep/backbranch. Entry+forwarders also pass
raw ELF no-subword-store opcode checks. Instruction bytes matched to disassembly.

Ten negative controls: consistent ELF/disassembly changes for missing terminal
barrier, direct target+4, wrong entry indirect register, wrong forwarded callback
register, return from entry, alternate wrapper return, escaping conditional
branch, subword store; plus stale disassembly and missing symbol. Reconstructed
test ELF contains archived actual function bodies only and is explicitly synthetic,
not a bootable/full PMU image. Actual result separately checks the real linked ELF.

This is compiler-shape-specific static inventory/range checking, not full
MicroBlaze semantics, symbolic dataflow, IRQ-check dominance, eventual termination
or callback identity proof. It does not authenticate a callback's effects or make
memset/exception/ROM paths safe. Locally contained loops can still fail liveness;
underlying callback can hang/trap. Dynamic metadata/software fault tests remain
separate evidence. No hardware gate was extended to accept this new profile.

No target source/image, firmware hook, physical backend, mailbox or HW changed.
No JTAG/UART/network/reset/register access. MUST NOT DEPLOY; DDR NOT_ADMITTED.
Next safe offline work: source/artifact-bound read-only composition audit gate
combining fresh layout/flow/store checks, with unconditional deployment refusal
and changed-source/helper/ELF negative controls. Hash provenance, independent
stuck-read recovery and PMU-to-AP0 visibility remain OPEN.
Reproduce: python -m unittest discover -s tests -p 'test_pit*.py' -v.
