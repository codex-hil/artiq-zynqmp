# KASLI04 → Genesys long fragmented DMA lifecycle PASS

Three two-fragment uploads (1010/10bytes each), nine plays (six via handle),
replacement plus erase/reupload PASS through native AUX. Physical input
measured522edges; all nine runs match expected widths4000/6000/8000mu,
periods16000/20000/24000mu and first delta1000120mu. Native operation order,
per-version trace IDs and error-free completion validated; no new checked
service/master faults. TSC/reset/DIO tests passed again.

Sorted04+Genesys leases covered full session/restoration. KASLI04 clock,
originalmux71 and mode10 restored; Genesys normalCoreDMA/analyzer/MonInj/
Ethernet restored at192.168.2.3; leases released. No01/03/Flash/OTP/SD/
GenesysSi writes. Bounded lifecycle proof, not capacity/throughput/phase/
jitter qualification. Next qualify native DMA error reporting/recovery on04;
active-delay fault lab remains separately gated by new idle-counter proof.
