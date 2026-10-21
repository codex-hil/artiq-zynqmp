# KASLI04 → Genesys native DMA lifecycle PASS

Exact previously qualified firmware/PL and idle proof; sorted shared04+Genesys
leases held through programming, tests and restoration. Standard CoreDMA
lifecycle passed three uploads/versions and nine plays (six via handle),
replacement plus erase/reupload. Physical input measured72edges total with
widths8000/16000/24000mu, periods80000/120000/160000mu; each first delta
1000120mu. Native AUX upload/play/status/erase sequence and trace IDs passed
with no new service/master faults. TSC/reset/DIO checks passed again.

KASLI04 clock/original mux71/mode10 and Genesys normal local CoreDMA/debug/
Ethernet restoration PASS at192.168.2.3; leases released. No01/03/Flash/OTP/
SD/GenesysSi writes. This is bounded lifecycle validation, not sustained DMA
throughput or deterministic phase proof. Next multi-packet trace upload/
fragmentation validation, then stability/link recovery.
