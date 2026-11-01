# Static PMU vector-selection trace — offline2026-11-01

SPDX-License-Identifier: LGPL-3.0-or-later

No hardware operation, GPO read/write, reset, vector patch or firmware change.
This trace preserves the prior UNKNOWN remap state. It does not claim to resolve
live routing from software metadata or previous successful runtime behavior.

## What the reviewed files show

The exact minimal audit ELF places reset/software/IRQ/hardware-exception vectors
at0xffdc0000/08/10/20. Their instructions branch to linked XPfw_Init,
XPfw_Exception, XPfw_InterruptHandler and XPfw_Exception_Handler respectively.
Archived disassembly records these local branches; it does not show whether a
physical exception fetches this aperture.

XPfw_Init initializes r1/r2/r13, programs stack-limit registers, clears BSS by u32
stores, calls XPfw_Main, then loops if it returns. No remap write appears in this
startup body's reviewed instructions. The retained original source set comprises
60 C/S units; lexical scan finds no GPO0/DEBUG_REMAP/ffd40010 reference. This is
not proof of no writes through generic MMIO/address aliases, ROM routines,
external loader/debug actions, earlier boot stages or unscanned inputs.

XPfw_CoreConfigure enables peripheral slave-error behavior/ECC interrupt handling,
starts interrupts and marks firmware present. XPfw_InterruptStart writes IRQ enable
and invokes the exception-enable API. Those source actions are not a documented
GPO remap transaction. The ROM service interface declares an extension table and
calls ROM services; a service-table declaration alone is not vector-selection proof.
Neither this scan nor ELF contains a complete observed ROM execution path.

BSP BaseVectorAddr=0xffd00000 remains distinct from linked0xffdc0000 vector bytes.
Do not patch one to match the other without establishing target aperture/ROM-loader
semantics. Source/layout/PC assumptions cannot substitute for hardware routing.

## Relevant register contract

UG1087rev1.11 specifies GPO0 at0xffd40010 as write-only. DEBUG_REMAP bit0 selects
ROM(default) versus RAM base-vector mapping for a64-byte region. The register
also includes PIT prescaler/control fields; a write updates all bits. Therefore
read-modify-write using a supposed readback cannot preserve unknown latch values.
No such operation is proposed or performed. [AMD GPO0 reference](https://docs.amd.com/r/en-US/ug1087-zynq-ultrascale-registers/GPO0-PMU_IOMODULE-Register?contentId=n1lYCViMc_vfwdPAscq~iA).

A documented reset value is not a current latch observation, especially across
retained state, debugger activity or distinct reset types. Existing historical
raw zero from this write-only address remains withdrawn as evidence. Do not use
FW_IS_PRESENT, a runtime UART banner, an ELF entry or sleep status to infer remap.

## Remaining boundary and next offline work

Actual vector source and ROM dispatch/forwarding remain UNKNOWN. Thus replacing
ELF vector bytes or linking a stackless entry does not establish it will receive
an exception or preserve production notification policy. No external PMU RAM
read/sleep/recovery permission follows from this trace.

Next safe offline step: inventory the declared ROM entry/service interfaces and
existing loader launch/PC assumptions, pin their source/linked dependencies and
state what is absent from accessible evidence. Do not execute ROM routines, read
ROM/PMU RAM through APB or inspect the write-only latch. If independent mapping
qualification cannot be designed within established recovery/ownership constraints,
leave hardware entry NOT_ADMITTED rather than guessing or changing policy.
