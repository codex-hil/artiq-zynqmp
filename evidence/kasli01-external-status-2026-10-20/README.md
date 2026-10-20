# KASLI01 external retry with read-only startup status

External AUX startup failed again. Post-failure DAP telemetry, captured
under the existing parent Genesys lease before restoration, confirms magic
0x44525430, monitor_reset=0, aux_in_reset=0, aux_rx_up=0. Link admission is
not satisfied. These sequential samples do not identify the exact earlier
failing poll or prove a cable/module fault. monitor_status is snapshot-based
and was not refreshed by this read-only script; its zero is not a live PHY
status diagnosis. No reset/RX-up checks were bypassed.

Master netboot/runtime/management/counter RPC passed again. External TSC/DIO/
DMA remain NOT_RUN. KASLI01 diagnostic plus volatile clock restoration PASS;
Genesys local runtime/debug/Ethernet restoration PASS at192.168.2.3. Both
leases released. No flash/OTP/SD/GenesysSi writes, no Kasli03/04 access.

The pinned Kasli target requests SFP1 then SFP2 for DRTIO, with SATA disabled.
Destination1 routing therefore uses the first DRTIO port, SFP1. Next physical
check is the KASLI01 SFP1-to-Genesys SFP connection, modules and fiber seating.
Do not run another identical load/test cycle until that path is confirmed.
