# KASLI04 → Genesys native distributed DMA PASS

Exact prior KASLI04 idle/TSC/snapshot/DIO/restoration proof checked before
physical trial; firmware/PL hashes unchanged. Sorted04+Genesys leases held
through programming, tests and restoration. Local management/counter,
external TSC/reset and two DIO kernels passed again.

Standard ARTIQ CoreDMA experiment uploaded the remote trace via native AUX,
played it on Genesys, checked completion and removed it. Physical TTL input
captured8edges, width8000mu, period80000mu, first delta1000120mu. Matching
upload/play/status/erase IDs and zero-error completion passed, no new native
service/master faults. This is one basic playback; fragmentation, repeated
lifecycle, fault handling and deterministic phase/jitter are not proved here.

KASLI04 clock/profile/PLL/originalmux71/mode10 restoration PASS. Genesys normal
local CoreDMA/analyzer/MonInj/Ethernet restoration PASS at192.168.2.3. Both
leases released, no01/03/Flash/OTP/SD/GenesysSi writes. Next bounded native DMA
lifecycle/fragmentation test and then link stability/recovery checks.
