# KASLI04 physical ARTIQ runtime qualification

PASS with exact04 DNA and user-confirmed SFP0 switch connection. Sorted
KASLI04+Genesys shared leases held through SRAM loading/testing/restoration;
Genesys was not accessed. Pinned no-EEMmux firmware and per-board MAC used.

Bounded retained TCP connection readiness enabled for initial boot and
post-Si5324 clock-switch reboot. Both RAM uploads/boot commands completed;
ARTIQ runtime startup PASS. Two standard artiq_coremgmt log connections PASS.
Two standard artiq_run counter/RPC kernels PASS; no TTL writes. This proves
master services/local counter execution, not external DRTIO/TSC/DIO/DMA.
Network root cause remains unproved; readiness addresses startup timing.

Temporary diagnostic restoration, exact clock profile/readback/ID/PLL and
coarse host-referenced frequency checks PASS; clock restore27.508s. Original
mux71 route restored with readback; mode10 restored and version/mode/idle
checked PASS. Absent EEMmux70 not accessed. No Flash/OTP/SD or01/03 writes.
Both leases released. Next one bounded external04SFP1-to-Genesys link/TSC/
reset/DIO idle qualification using current guarded restoration.
