# One-shot session binding and isolated PMU audit link — 2026-10-27

Offline, no HW/MMIO backend or deployment. New C session state binds nonzero
boot/nonce/sequence and allows one accepted execution. Wrong identity rejects
before backend. Accepted request consumes state before first callback; success,
IO failure or invalid backend cannot be retried/rearmed. Receipt echoes identity,
keeps low-level status separate from accepted, and never grants DDR writes.
No reset/release API. Local storage must start zero and be exclusively owned;
caller could overwrite it, concurrent threads/cores are not made atomic, tokens
are not authenticated or independent hardware boot evidence.

Actual optimized and ASan/UBSan C tests PASS for stale boot/nonce/sequence,
duplicate/rearm, callback reentry, write failure and null backend consumption.
Prior strict C optimized/sanitized fixtures also PASS. Host tests do not model
MicroBlaze concurrency or prove physical session identity.

Replayed actual PMU compile/link recipe with both components and -u retention
for arm/execute. Existing PMU entry/main/guard do not call them. No callbacks point
to MMIO. Audit-only ELF linked with original local linker script and BSP/libs;
layout checker PASS. Added fstack-usage/save-temps for LTO audit; compiler warns
pipe ignored/serial2LTRANS, no compile/link failure. No existing build overwritten.
This audit image is NOT_DEPLOYABLE and not a new release candidate.

FinalLTO frames arm0,execute172,snapshot48 bytes; strict hold inlined into execute.
Internal nested220 excludes caller/backend/helper contributions. Compiler-generated
memset dependency resolves from linked library; previous standalone164-byte estimate
is not transferred to this link. Text76124bytes; actual map/sections/layout and
stack reports retained, full artifact hash local. No full execution-path/ROM/
exception/competing-writer or all-master DDR exclusion is established.

Next offline: specify bounded read/write/timer backend and its exact address/
callback table validation, source-core exclusion and restoration accessibility
before any guarded integration. No live AIB writes admitted by session/link PASS.
Normal runtime untouched; DDR NOT_RUN/NOT_ADMITTED.
