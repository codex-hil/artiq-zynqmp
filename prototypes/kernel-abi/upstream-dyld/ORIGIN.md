Copied from m-labs/artiq-zynq @ 15c856f315969b5c1d01d2917ed52f1b0f199677, src/libdyld. LGPL-3.0, original license retained.

Changes: privileged Cortex-A9 cache operations in reloc.rs call cache_sync instead. lib.rs supplies a Linux ARM cacheflush adapter for the userspace test, or DSB/ISB for the bare-metal test with caches disabled. Cargo template became a pinned local manifest. All other loader source files are unchanged.

These adapters are for cache/MMU-disabled diagnostic probes only (QEMU and the physical A53 CPU1 diagnostic validated on 2026-10-07). They are not an implementation of ZynqMP cache maintenance or a hardened loader. Only locally compiled trusted kernels are passed to it. Production integration needs the hardware cache/MMU policy and real exception/RPC support.
