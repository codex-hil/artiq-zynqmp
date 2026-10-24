# PMU ROM/RAM vector boundary — 2026-10-24

Offline exact ELF and installed BSP inspection. No HW access or ROM reads.
BSP XPAR_PSU_PMU_BASE_VECTORS=4291821568=0xffd00000. UG1085v2.5p117
maps that address to PMU ROM, PMU-only local bus. Printed p114 describes ROM
boot/services/interrupt-vector responsibility. ELF vectors instead start at
0xffdc0000 in RAM; previous audits describe RAM stubs and their reachable code.
They do not establish ROM event entry/forwarding to these stubs.

Official source inspected from previously downloaded PDF:
https://docs.amd.com/api/khub/documents/xzMsp_c5sG9J6A3u7NkJYQ/content?Ft-Calling-App=ft

There is no break-vector section at RAM+0x18. The first ELF PT_LOAD contains
8 zero file bytes at0xffdc0018..20. This is not an installed safe handler or
proof of which address a physical break executes. Do not write a guessed handler
or infer ROM forwarding from linker layout. Hardware fault-tolerant parameter
was not established from xparameters.h; absence of a macro is not value zero.
Stack protection1 and several exception parameters are present, but do not close
ROM/reset/NMI behavior or all memory effective addresses.

Correction/qualification of prior reports: hardware entry EE/EIP architecture
and RAM handler stack estimates are conditional on the actual ROM->RAM bridge.
They are not a proven complete event path for this hard PMU core. Earlier local
CFG/table/frame facts remain valid for their linked RAM functions. Physical
nonce/MSR guard capture and restoration PASS remain unchanged.

Next offline: search maintained AMD PMU/ROM API sources and versioned PMU design
documentation for event forwarding/stack/reset-break policy. Record inaccessible
or undocumented implementation explicitly. No private alias/forced ROM access,
no arbitrary break injection, no exception masking, no unchanged HW retry.
DDR remains NOT_ADMITTED; normal runtime unchanged and not rechecked here.
