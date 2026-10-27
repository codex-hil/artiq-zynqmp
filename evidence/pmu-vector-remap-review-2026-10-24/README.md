# PMU vector remap and ROM extensions — 2026-10-24

CORRECTION2026-10-27: GPO0 is write-only per UG1087. Readword0 does NOT prove
ROM/RAM selection. Mapping remains UNKNOWN; raw results preserved. See
[write-only correction](../pmu-writeonly-correction-2026-10-27/README.md).


Offline documentation/source review, no HW access. Important qualification to
previous ROM/RAM report: configured BASE_VECTORS=0xffd00000 alone does not prove
ROM receives live events. UG1085v2.5p119 GPO0[0] selects default ROM vs remapped
RAM for the first64vector bytes. Local pmu_iomodule.h defines DEBUG_REMAP mask1.
No value of this PMU-local bit was captured in the guard hardware evidence.
Current mapping therefore remains UNKNOWN, rather than established ROM entry.

Official primary documentation:
https://docs.amd.com/api/khub/documents/xzMsp_c5sG9J6A3u7NkJYQ/content?Ft-Calling-App=ft

Exact candidate xpfw_rom_interface.h describes an extension table checked by ROM
before eligible default services; non-null entries override services and receive
a callback to the original implementation. IRQ infrastructure is included. This
is not proof all exception/break events use the extension mechanism. The
.xpbr_serv_ext_tbl section lies at0xffddf6e0, distinct from RAM vector stubs.
Declared table and runtime supply-check hook assignment do not establish general
exception forwarding. No live extension-table state was captured.

The inspected PMU app C/assembly has no textual GPO0 access, and the boot launcher
contains download/start without an explicit remap write. Neither observation
excludes loader/debugger/ROM or linked BSP effects. Do not infer reset value or
quiet state from absent source references. No remap or fault-tolerance change is
authorized by this review, and zero RAM break-slot bytes remain unqualified.

Next useful offline action: audit exact linked startup/BSP and downloaded XSDB
flow for remap effects, then prepare a bounded PMU-local read-only telemetry field
for GPO0 if needed. Such a field needs a fresh default-disabled candidate, linked
read-address checks, updated manifests, lease/storage/restoration gates before
physical use. Do not repeat failed AP0 private alias access or write GPO0 to
force a convenient map. DDR remains NOT_ADMITTED; baseline untouched.
