# PMU initial configuration and EE/EIP review — offline2026-11-01

SPDX-License-Identifier: LGPL-3.0-or-later

This is software-data/architecture review, not a live CPU/ROM/vector observation.
No MSR writes, exception disable, vector replacement, physical fault or hardware
access. Current155-test suite is unchanged and not rerun; target offsetof/sizeof
assertions for12 selected fields passed using the actual BSP/compiler flags.

## Initial linked software configuration

In the minimal audit ELF, XMicroblaze_ConfigTable is at ffdd9458/312 bytes.
Field offsets are checked with target C static assertions, then values read from
unique file-backed ELF bytes. These are software metadata, not PVR/hardware proof.

| Field | Initial value |
|---|---|
| UnalignedExceptions |1 |
| IllOpcodeException |1 |
| UseStackProtection |1 |
| IopbBusException / DopbBusException |0 /0 |
| ExceptionsInDelaySlots |0 |
| UseMsrInstr / UseInterrupt |1 /1 |
| UseMmu |0 |
| UseExtBrk / UseExtNmBrk |0 /0 |
| BaseVectorAddr |0xffd00000 |

Actual ELF vector sections begin at ff dc0000 (reset), ff dc0008 (software),
ff dc0010 (IRQ), ff dc0020 (hardware exception), written without spaces as
0xffdc0000,0xffdc0008,0xffdc0010,0xffdc0020. The BaseVectorAddr metadata differs
from the linked aperture. Do not correct the table, relocate vectors or assume
one is active from this difference alone. It requires tracing target ROM/RAM
shadow/vector selection and the approved entry path. GPO0 is write-only in prior
PMU review; a zero read cannot establish its latch state. No read/write attempted.

The table's UseMmu=0 means the built software describes no MMU, not that physical
exception routing or MMU absence has been verified. External-break fields0 do not
prove board/platform/debug routes are excluded. C_FAULT_TOLERANT is not established
by these selected fields; never infer it from handler code or an absent symbol.

## What architecture documentation supports

UG9842024.1 identifies EIP as exception-in-progress, EE as exception enable and IE
as interrupt enable. MMU exceptions are not suppressed by EE. This distinction
prevents treating the normal IE-only clear as general exception exclusion.
[Machine Status Register](https://docs.amd.com/r/2024.1-English/ug984-vivado-microblaze-ref/Machine-Status-Register).

The accessible official UG9842020.2 hardware-exception pseudocode clears EE and
sets EIP on hardware exception entry. This is an architectural transition, not a
software lock or proof of this PMU's observed entry state. The generic2024.1
Equivalent-Pseudocode URL returned IRQ pseudocode; its exception-specific content
link could not be retrieved, so it is NOT misattributed as hardware-entry evidence.
[Official UG9842020.2 content](https://docs.amd.com/api/khub/documents/cvcQle7aFAI5wibwmAtbKA/content).

UG9842024.1 documents a conditional halt/MB_Error outcome for specified second
faults when C_FAULT_TOLERANT=1 and EIP set/EE clear. Since that configuration is
not proved here, this is a conditional hazard, not guaranteed fail-stop/recovery
or a basis to enable/disable anything. [Exception Causes](https://docs.amd.com/r/2024.1-English/ug984-vivado-microblaze-ref/Exception-Causes).

## Consequences for the candidate and model

The assembly candidate reads post-entry special registers and never changes EE,
EIP or IE. It is not installed at a vector. There is no proof that a requested
fault reaches it, that a subsequent event cannot interrupt it, or that a committed
record retains first-fault identity. Software-vector entry is not automatically
hardware-exception entry and must not inherit EE/EIP assumptions.

The prior nonreturning nested model remains a conditional control-flow class;
the forbidden resumed-outer counterexample stays explicitly non-physical. Neither
metadata nor EE/EIP documentation upgrades it to hardware reentry exclusion.
Store/fence faults can prevent receipt completion. No sleep/APB-read lifetime,
notification equivalence or arbitrary-hang recovery follows.

Next safe offline step: trace existing PMU vendor startup/ROM-RAM vector-selection
writes and linker/entry assumptions, record exact source/disassembly dependencies
without reading write-only registers or changing hardware. Resolve metadata vs
linked aperture as an evidence question, not by patching working configuration.
All vector/HW entry and deployment decisions remain outside this review.
