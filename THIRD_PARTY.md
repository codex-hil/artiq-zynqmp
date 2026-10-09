# Attribution and licensing boundaries

This is a continuation of [Piotr Jedyk’s artiq-new](https://github.com/pjedyk/artiq-new), based on `wip@b25e75b`. Git history and authorship are preserved. It is an experimental hardware port, not an official M-Labs release.

| Component | License / attribution |
|---|---|
| Original Piotr snapshot and modifications to its files | No repository-wide license found at the pinned snapshot. Original rights remain with the authors; obtaining an explicit license grant is outstanding. |
| New original contributions | LGPL-3.0-or-later; scope listed in `docs/NEW_FILES_LICENSE.txt`, subject to existing third-party notices. |
| ARTIQ / artiq-zynq loader, DMA and runtime sources | M-Labs and contributors; preserve the accompanying LGPL-3 notices and source attribution. |
| LLVM libunwind | See `boards/genesys_zu-5ev/3_kernel/llvm_libunwind/LICENSE.TXT`. |
| Rust-derived sources | Preserve their MIT/Apache notices and included license texts. |
| AMD/Xilinx and Digilent sources | Per-file notices and upstream licenses apply; see source manifests and file headers. |
| Migen and other submodules | Separate upstream licenses; not relicensed by this project. |
| Vivado and generated FPGA IP | Proprietary tooling; obtain separately from AMD. No installer, license key or tool installation is distributed here. |

Do not interpret public GitHub availability as an additional license grant for the original unlicensed snapshot. Licensing that part remains necessary before calling the entire combined port fully open source.

Pinned origins and revisions are in [docs/SOURCES.md](docs/SOURCES.md), `evidence/sources.json`, and subsystem READMEs. Laboratory evidence includes private-network addresses, board serials and historical host paths for reproducibility; these are not portable defaults. Hardware tests must select your own cable and UART explicitly.
