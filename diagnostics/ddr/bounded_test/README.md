# Bounded DDR pattern engine — offline only

`pattern.c` is a freestanding algorithm, not a bootable diagnostic or permission
to access board memory. No physical memory backend, cache maintenance or hardware loader is supplied.
The optional OCM model image below adds startup/stack/vectors for model I/O only.

The caller supplies up to 8192 unique aligned 64-bit addresses (64 KiB of tested
words). The engine validates the complete list before any I/O, rejecting the
MMIO gap and the ends of both configured DDR windows. Address validity is only
geometry validation: **it does not establish ownership or a safe test range**.
All code, address list, callbacks, report and stack must eventually reside in
verified OCM outside the tested DDR; this object does not establish that layout.

Four phases write zero, all ones, address-derived tags, and complemented tags.
Each phase writes ALL locations, invokes the barrier, then reads ALL locations;
this ordering detects sparse address aliases that immediate write/read misses.
The first callback fault or mismatch stops execution and reports phase, address,
expected/actual data and completed-operation counts. Failed read does not make
`actual` valid. Contents are destroyed; no original-content restoration is done.

Callbacks must return and be bounded. A finite operation count cannot interrupt
a stalled AXI load/store. The future physical backend needs exception capture,
a reviewed timeout/recovery strategy and an external lifecycle deadline. A host
model callback is not cache/MMU/DDR hardware validation.

Run host controls with `python3 -m unittest discover -s tests -p test_ddr_pattern.py -v`
from the repository. They compile the actual C engine with GCC and exercise two
windows, gap/alignment/bounds/duplicate rejection without I/O, alias injection,
phase ordering and first-fault termination.

AArch64 object compilation (not linking/boot):

```sh
/srv/codex-hil-data/artiq-zynqmp/toolchains/abi-verified/bin/clang-irrt \
  --target=aarch64-none-elf -ffreestanding -fno-builtin -fno-stack-protector \
  -mgeneral-regs-only -O2 -Wall -Wextra -Werror \
  -c diagnostics/ddr/bounded_test/pattern.c -o /FRESH_OUTPUT/pattern.o
```

Next integrate the existing exception-aware OCM layout and an explicit admission
policy. PMU/secondary-core access and preconfiguration transaction history remain
unresolved. Do not run this engine on Genesys before those requirements close.


## OCM model image

`bash scripts/build_ddr_ocm_model.sh /FRESH_OUTPUT` builds an AArch64 ELF
without hardware access. Vectors start0xfffc8000, entry0xfffc8800, stack
0xfffe0000..0xfffe4000. The linker and existing layout checker reject non-OCM
load extents and misplaced vectors/BSS/stack. No undefined runtime symbols.

Startup checks EL3, installs/readbacks VBAR_EL3 and rejects active SCTLR M/C/I
at EL3/2/1 or unexpected D/I/F masks. It does not disable caches/MMU or alter
interrupt masks. It clears only its OCM BSS and calls `ocm_model_main`.
Exceptions retain slot/ESR/FAR/ELR/SPSR/DAIF in registers and stop; no recovery
or hardware SError coverage is claimed. Debugger entry-state/OCM ownership
admission and a dedicated loader still need review before A53 execution.

The four apparent DDR addresses are lookup keys into four OCM model cells.
There is no pointer cast or physical DDR callback. Model PASS means the engine
and local callbacks agree, never that physical DDR was exercised. Host execution
and link layout are tested; this image has NOT run on A53 or QEMU.
