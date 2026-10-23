# PMU guard RAM arbitration review — 2026-10-23

Offline review only. The failed physical capture remains FAIL; guard entry and
IE clearing remain NOT_PROVEN. No hardware access or image changes in this review.

## Primary documentation and local code

AMD UG1085 v2.5 (2025-03-21), printed page 113, PMU RAM:
https://docs.amd.com/api/khub/documents/xzMsp_c5sG9J6A3u7NkJYQ/content?Ft-Calling-App=ft

External APB RAM access requires the PMU processor to sleep. Running instruction
fetches can starve it; arbitration favors PMU data, then instructions, then external
access. The downloaded official PDF was independently checked with pdftotext;
its hash is recorded in inputs.json. This explains a defect in the test design:
a no-load/store loop is still an instruction-fetch loop. It is consistent with
the AP0 timeout, not a measurement of arbitration or proof of guard execution.

AMD UG984 2025.2, Software Controlled:
https://docs.amd.com/r/2025.2-English/ug984-vivado-microblaze-ref/Software-Controlled

Sleep is the mbar 16 pseudo-instruction. It halts the pipeline after external
access completion. A Wakeup input resumes execution after that instruction;
debugger wakeup can also require software to sleep again. Wakeup wiring and
interrupt acceptance are separate concerns; disabling IE does not establish
that the processor cannot wake. An asserted wake input could defeat residency.

The installed AMD BSP mb_interface.h:138 maps mb_sleep() to sleep. The original
PMU xpfw_core.c:371 uses mb_sleep() before scheduler processing. The failed
linked guard ends at 0xffdc4734 with nop and a backward branch, with no sleep.

## Specifically changed candidate requirements

Prepare an explicit, default-off sleep/back-branch terminal guard. Preserve
publication ordering, nonce, MSR checks, ACK=0 and unresolved=0x7f. Wakeup must
return only to sleep, never scheduler/request dispatch or ordinary firmware.
Update the linked instruction checker to prove this precise terminal and reject
returns, external branches or unexpected memory operations. Rebuild both enabled
and disabled images and retain old failed artifacts/manifests unchanged.

Before hardware: fresh exact image/symbol/disassembly/helper pins, linked flow
and negative controls, unchanged bounded PMU debugger recovery, storage reserves,
and the shared Genesys lease. Establish a bounded observation strategy accounting
for PMU wake inputs; do not force or repeat external RAM reads after a timeout.
A successful capture would still not admit destructive DDR testing.

Normal runtime was restored by the previous physical trial; this review does
not perform a fresh health check. Full DDR remains NOT_RUN/NOT_ADMITTED.
