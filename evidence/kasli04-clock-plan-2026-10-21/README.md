# KASLI04 restoration admission plan (offline)

The existing planner/baseline binding now accepts exact KASLI04 DNA. Plan
contains all23 writable configuration registers from the stable physical
snapshot, excludes status/identity/command replay, and requires fresh ICAL.
Only mux0x71 exists in this board routing profile; mux0x70 is user-confirmed
removed. Runtime lease scope is Genesys plus04, not01/03.

This is not a physically exercised reset/restore procedure. The existing
UART diagnostic capture/runtime wrappers still refuse04; do not pass this
plan to another board or bypass their selection. Before any runtime action,
implement a bounded04-specific wrapper preserving/restoring exact retained
mode10 SRAM and routing. Read-only FTDI snapshot alone is insufficient.

Six existing/new clock selection/restoration tests passed, including exact
04 baseline acceptance, wrong-board and changed-profile rejection. FPGA
build remains in progress independently; no hardware access this checkpoint.
