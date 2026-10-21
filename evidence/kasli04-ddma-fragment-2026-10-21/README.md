# KASLI04 → Genesys fragmented native DMA PASS

Qualified firmware/PL and exact idle proof reused under sorted04+Genesys
leases. Standard CoreDMA trace crossed the native AUX fragment boundary: two
upload packets1010/10bytes with one trace ID, then play/status/erase sequence
PASS. Physical TTL input measured58edges, width8000mu, period16000mu, first
delta1000120mu. No new native service/master faults; TSC/reset/DIO repeated
PASS. This is one two-fragment trace, not maximum capacity/throughput proof.

Both-board restoration PASS:04clock/originalmux71/mode10, Genesys normal
localCoreDMA/analyzer/MonInj/Ethernet192.168.2.3. Leases released, no01/03/
Flash/OTP/SD/GenesysSi writes. Next link stability/forced recovery checks.
