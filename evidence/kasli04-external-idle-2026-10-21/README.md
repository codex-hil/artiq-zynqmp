# KASLI04 SFP1 → Genesys external DRTIO/DIO PASS

Bounded physical session PASS under sorted KASLI04+Genesys shared leases
through programming, UART/network/kernel tests and both-board restoration.
Exact KASLI04 DNA confirmed; no01/03 access. Uses the existing qualified
direct-destination1 laboratory satellite, not a complete upstream target.

Upstream AUX echo and master link initialization PASS; TSC load/ACK once
and four monotonic fine3 snapshots PASS. Two native core.reset kernels
with preserved PHY/reset acknowledgement PASS. Two standard ARTIQ DIO
kernels each generated8pulses through external DRTIO to Genesys JB1,
captured on jumpered JB2, spacing100000mu, physical resolution8ns. No new
firmware send/RX errors. Absolute phase, jitter and deterministic link
latency NOT_MEASURED. DMA playback and broader satellite services NOT_RUN.

KASLI04 diagnostic, volatile clock/profile/PLL/frequency/original mux71
routing and retained mode10 restoration PASS. Genesys normal local
CoreDMA/analyzer/MonInj/Ethernet restoration PASS at192.168.2.3. Leases
released. No flash/OTP/SD/Genesys Si or other-board writes.

Next qualify native distributed DMA using this exact idle DIO/snapshot/
restoration proof and same firmware/PL hashes; then stability/reset cycles.
