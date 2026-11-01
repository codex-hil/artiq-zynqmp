# Static ROM service and loader assumptions — offline2026-11-01

SPDX-License-Identifier: LGPL-3.0-or-later

No loader executed, hardware/ROM/PMU RAM read, remap write, reset, vector patch
or firmware change. This review describes accessible declarations/artifacts only.
It does not resolve active vector source or qualify installing the audit handler.

## Declared service interface versus observed execution

Vendor xpfw_rom_interface.h describes ROM services/hooks as extendable through a
RAM function-pointer table: ROM checks the selected entry and may call firmware
instead of a default service, passing a callback to the default implementation.
The comment includes IRQ routing infrastructure. This is an interface contract,
not evidence of the device's ROM instructions, version or executed dispatch.

The linker binds XpbrServHndlrTbl to absolute0xffd07bc8; that declaration supplies
addresses for calls, not the ROM bytes at that address. No ROM instruction read
or execution was attempted. The RAM XpbrServExtTbl is256 pointer entries/1024 bytes
at fixed0xffddf6e0. In the minimal audit ELF its initial bytes are all zero; hash
recorded in evidence. That does not establish current RAM contents or a no-hook
claim. pm_power.c writes a configured supply-check hook into this table at runtime.
Other code, ROM/earlier boot/debug routes remain outside the static observation.

Do not equate an empty initial extension table, a firmware-present flag or a
valid ELF entry with proof that exceptions use linked RAM vector instructions.
Service overrides and vector remap are distinct evidence questions. No conclusion
about hardware exception forwarding follows solely from the IRQ service comment.

## What the existing loader text does

load_rtio_runtime.py invokes run_boot_firmware.tcl with normal PMU/FSBL artifacts,
then proceeds with PL/kernel/debug services. In the reviewed Tcl, target selection
is cable-qualified; it selects alternate JTAG/debug access, stops/selects the PMU,
downloads the supplied ELF and continues before loading FSBL on A53. These command
lines were inventoried without executing them or observing PC/ROM state.

There is no explicit GPO0/DEBUG_REMAP transaction in that loader script. This is
not a guarantee that debugger commands, earlier boot or hidden platform behavior
cannot affect routing. XSDB dow/con effects are not being substituted for a live
PC/vector proof. restart_pmu_for_restore.tcl is separately inventoried; its current
text is not proof of an arbitrary-fault recovery path.

The minimal audit ELF declares entry0xffdc0050 (XPfw_Init) and vector bytes at
0xffdc0000. BSP BaseVectorAddr remains0xffd00000. No script/metadata item above
proves which aperture is selected for a real event. Prior runtime success proves
only its dated tested behaviors, not execution of the new stackless candidate.
The standalone synthetic entry-link fixture remains non-PMU and uninstalled.

## Result and next bounded offline step

Active remap/ROM dispatch/exception entry remains UNKNOWN. The accessible static
chain ends at ROM/loader execution and actual vector routing. Do not fill that
boundary with assumptions, a write-only GPO read, vector patch or disabling faults.

Next safe offline work: consolidate a readiness/decision matrix and a non-executing
qualification proposal listing evidence needed before an isolated hardware-entry
trial: exact target identity/lease, baseline restoration/recovery limits, image/
slot ownership, ROM/vector mechanism, preserved error notification and forbidden
APB access. Separate what can be checked offline from actions requiring an explicit
policy decision and independently safe hardware plan. Do not run a trial merely
because standalone assembly, digest pipeline or format tests pass.
