# Volatile record word initialization — offline, 2026-10-30

pit_capture now initializes its48-byte local record through an aligned C union
with12 uint32_t representation words, using explicit volatile32-bit stores after
plan validation/consumption. No aggregate record={0} clear remains. C host tests
(including optimized/sanitizer capture/composition/error paths) pass:82 PIT tests.
No hardware access, callback semantics or record bytes changed intentionally.

Fresh11-custom-unit LTO link/no undefined symbols/layout/project-function store
checks PASS. Entry has an exact12-word loop (indexed sw,4-byte stride), count12,
baseSP+28; eight initializer instruction pins checked against actual ELF bytes.
Entry has11 direct calls:3observe/1disable/1read/3write/2barrier/1terminal, with no
memset target. Library memset remains linked for other vendor/runtime uses; this
is not a global binary no-byte-store claim. Indirect external callbacks/exception
paths and physical no-wake/consumer/recovery requirements remain unqualified.

Four consistent ELF+listing controls reject count13, wrong stride, byte store
and reinjected memset call. review.py checks exact initializer/call inventory,
not generic CFG/dataflow/liveness. Frame entry296+read52+raw0=348bytes internal
subtotal, excluding caller/other callbacks/exceptions. Earlier344 subtotal applies
to old build only. Old exact MMIO pin checker rejects new code/layout as intended.

Old ELF/source evidence and frozen snapshots preserved. Working pit_capture source
has changed, so previous working-tree source manifests are stale and must refuse;
do not repin old claims. Next safe offline work is a new explicit word-init MMIO
profile with complete20 custom source/header closure and artifact/helper pins,
new exact body controls and unconditional deployment refusal. No physical trial.
