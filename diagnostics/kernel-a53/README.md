# Physical A53 kernel loader diagnostic (CPU1)

This reuses the already tested NAC3/ARTIQ ABI prototype and the preserved
M-Labs ARM ELF loader. **It is not the network kernel runtime**. It runs a
trusted embedded ELF on physical A53 CPU1, EL3/AArch64 → EL1/AArch32, while
CPU0's AArch64 AMD/lwIP Rust management application remains running.
Kernel output calls use a checked memory model and do not drive TTL pins.
A separate diagnostic reads the real PL RTIO counter from AArch32 CPU1.

The positive variant is compiled using actual upstream Core/EnvExperiment/
TTLOut classes, checks i64, hard-float, NEON and timeline, and handles only
empty automatic writeback. The negative variant changes an i64 argument and
must fail an ABI assertion, **not** a hardware exception. Neither exercises
application RPC or exception unwinding. No physical experiment is claimed.

## Reproduce

Prepare modules with `prototypes/kernel-abi/README.md`. Reuse the pinned
compiler, upstream source revisions and open-source tools documented there.
Start management and local-rtio using `diagnostics/services/README.md` first.
CPU1 must be available for this exclusive diagnostic; CPU0 is not reset.

```sh
export RUSTUP_HOME=/srv/codex-hil-data/artiq-zynqmp/rustup
scripts/build_kernel_hardware_probe.sh \
  "$ABI_RESULTS/artiq/module.elf" "$ABI_TOOLS" "$POSITIVE" "$CSR_MAP"
scripts/build_kernel_hardware_probe.sh \
  "$ABI_RESULTS/negative/module.elf" "$ABI_TOOLS" "$NEGATIVE" "$CSR_MAP"
make test-hw-kernel-cpu1 PYTHON=/path/to/venv/bin/python \
  JTAG_SERVER="$JTAG_SERVER" JTAG_CABLE=210383B7F02DA SERIAL="$SERIAL" \
  BOARD_IP="$BOARD_IP" KERNEL_POSITIVE="$POSITIVE" KERNEL_NEGATIVE="$NEGATIVE" \
  O=/large-disk/results
```

`CSR_MAP` must be the actual local-rtio generated 32-bit map at 0xA0000000.
The runner checks ELF architecture and segment bounds before JTAG loading,
clears the result mailbox, captures UART, verifies actual completion/rejection
and confirms CPU0 management before/after both cases. SHA-256 manifests,
UART/JTAG logs and structured hardware results identify the tested artifacts.
CPU1 parks after completion (also after the expected negative assertion).

Dedicated diagnostic memory: startup at 0x20000000, status/trap mailbox at
0x200FF000, ARM image/heap/stack in 0x20200000–0x20400000. The current CPU0
image uses low DDR; this reservation must be checked again when changing its
linker map. This is not yet a production memory map or allocator.

## Physical fixes compared with QEMU

- Clear SCTLR_EL1.V: reset high-vector state otherwise bypassed local VBAR.
- Align embedded ELF to four bytes. The upstream loader reads headers as
  words; MMU-off device memory on the real A53 rejected an unaligned load
  that QEMU allowed. Fault PC/LR was captured, then the alignment fixed.
- XSDB's automatic CPU cache synchronization could not switch privileged
  state after CPU1 entered AArch32. Mailbox writes use bypass-cache-sync;
  reads use physical DAP AP0. This applies only to the dedicated uncached
  diagnostic mailbox. It is not a production cache-coherency solution.
- Exceptions record LR/SPSR and terminate the diagnostic; the negative test
  rejects a nonzero trap LR, so a hardware trap cannot masquerade as success.

Next: production memory/cache policy and inter-core channel, network kernel
upload/load/run, real RTIO exports, application RPC and exception handling.
An AArch64 function pointer cannot directly call this ELF32 kernel; keep the
execution-state transition explicit. The successful physical test supports
reuse of the Cortex-A9 compiler/loader rather than inventing an AArch64 ABI.
