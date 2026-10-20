# KASLI01 master CPU build and board-specific guard

CPU build and embedded boot ROM checks passed. See `cpu-qualification.json`
for artifact hashes and memory-map comparison. The existing isolated source
is recorded in `../kasli01-master-source-2026-10-20`.

The board selector binds DNA 0x007865085f704854, volatile MAC
02:4b:01:48:48:54 and link-local fe80::4b:1ff:fe48:4854. Its runtime
lease scope is KASLI01 plus Genesys; KASLI03/04 are not accessed. Clock
inputs must match this board, the baseline hash and the exact physically
validated restoration profile. Existing verified flash-backup metadata is
checked before loading SRAM because the restoration programmer requires it.
No flash writes are performed. Historical KASLI03 selection remains available
for offline comparison; current allocation prohibits live use of that board.

All 13 `test_kasli_*.py` tests passed. The historical qualified master
profile also passed offline preflight. These are software checks, not
physical netboot or DRTIO qualification of KASLI01.

`build_gateware.sh` is the launched Vivado recipe. At this checkpoint synthesis
passed with zero critical warnings/errors; implementation is still running.
No FPGA image was loaded and no hardware was accessed in this checkpoint.
Full build qualification and a bounded KASLI01 netboot/restoration test remain.
