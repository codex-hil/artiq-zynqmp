# Runtime protocol audit —2026-10-22

This is a code audit against the checked-out ARTIQ revision
`1461cf90953ed9972c040b263e5a11c9ebc9e41a`, not a claim of compatibility with
all future releases. The integration uses CPU0 AMD/lwIP framing and an AArch32
CPU1 worker; it is not the complete upstream AArch64 runtime.

| Interface | Implemented path | Boundary |
|---|---|---|
| Core handshake | `ARTIQ coredev\n`, little-endian marker; SystemInfo replies `ARZQ` | Host accepts this runtime ID without AROR gateware-version/clean-finish fields; do not append those fields to this reply |
| Kernel loading | LoadKernel/LoadCompleted/LoadFailed, maximum1MiB ELF upload | CPU1 must be available; oversized/empty uploads are rejected |
| Execution | RunKernel, worker completion and native exception events | One owner; worker death/recovery is distinct from a normal caught exception |
| RPC arguments | Preserved M-Labs serializer, event body limited to4096bytes | This is not a promise that every host object fits or is supported |
| RPC results | Transport/worker accept `n`, `b`, `i`, `I`, `u`, `U`, `f`; pinned host emits `n`, `b`, `i`, `I`, `f` | CPU0 and CPU1 both restrict replies to scalars; list/tuple/array/string results are not implemented |
| Host RPC exception | Fixed48-byte ARM-layout bridge to CPU1 native unwinder | Does not establish arbitrary exception payload compatibility |
| Subkernels | No CPU0 SubkernelUpload branch | Unsupported; adding host acceptance alone would be incorrect |
| Management | GetLog, ClearLog and selected read-only metadata | Remote management destination, config writes and other commands are rejected |

The scalar-only restriction appears in both
`2_firmware_a53/c/kernel_lwip.c` and `3_kernel/src/lib.rs` under the board directory.
CPU1 checks the requested return tag before serializing an RPC event. Its
`rpc_recv` delegates scalar decoding to the preserved upstream code and rejects
nested allocations. CPU0 accepts a one-byte return-tag descriptor and only
forwards scalar bytes. Complex results therefore require a coordinated change
to framing, allocation/ownership, worker receive ABI and bounded error handling.
A host-only workaround would not implement them.

## Diagnostic correction

The management startup log still stated that TTL was disabled and exceptions
were pending. That historical statement was wrong for the later qualified
workers. It now reports that RTIO/DMA and exception capabilities depend on the
loaded worker and gateware, and explicitly lists complex RPC results/subkernels
as unsupported. No capability is inferred merely because CPU1 reached ready.
This source correction has not been deployed; qualified binaries and release
manifests retain their original bytes.

## Validation and next implementation step

Existing management parser tests passed6/6 using `cargo test --lib`. An initial
plain `cargo test` also tried to build the no_std static library for a host with
unwinding enabled and failed; `--lib` selects the intended host unit-test harness.
This is not a firmware cross-build or new hardware test.

Before extending RPC results, extract the CPU0 reply parser into a host-testable
component and exercise real pinned host byte streams, fragmentation, incorrect
lengths/tags and abort/recovery. Then select a bounded result type and update the
CPU1 allocation/ownership path. Keep the currently qualified runtime available
for restoration and qualify changed binaries separately.

## Extracted scalar parser checkpoint

`2_firmware_a53/c/rpc_reply.h` now owns the bounded scalar reply-body parser.
CPU0 uses it directly; `attach_a53_services.py` copies the header with the
transport source. It parses the four-byte little-endian tag-descriptor length,
requires exactly one supported scalar tag and accepts at most8payload bytes.
No worker command is issued until the reply is complete. Invalid input remains
invalid until initialization; network recovery/ownership remains in the existing
transport. This does not add complex results or authenticate a peer.

`tests/test_rpc_reply.py` compiles this same header with host C and obtains
wire bodies through the checked-out `CommKernel._write_bytes` and
`_send_rpc_value`. Nine real scalar cases cover signed limits, bool, None and
floating point; every truncated prefix remains incomplete. Wrong tag lengths,
unsupported tags and bytes after completion are rejected. These are parser
controls, not an end-to-end TCP/worker recovery test. Run with the ARTIQ host
Python environment:

```sh
/path/to/artiq-host/bin/python -m unittest discover -s tests -p test_rpc_reply.py
```

Both tests PASS. The updated complete transport translation unit also compiles
for AArch64 using the retained qualified BSP include/compile flags and a fresh
object output. Evidence: `evidence/rpc-reply-parser-2026-10-22/`.
No full firmware link, deployment or hardware qualification has occurred.
The source has changed; old source-equivalence statements and qualified binary
hashes describe their original checkpoints, not this newly edited transport.
Next validate transport callbacks/abort behavior and build the full CPU0 image
before a bounded hardware qualification of the changed source.
