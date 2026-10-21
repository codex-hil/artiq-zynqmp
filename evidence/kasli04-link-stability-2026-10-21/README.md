# KASLI04 → Genesys DIO stability and link recovery PASS

Sorted shared04+Genesys leases held through programming, tests and restoration.
Two stability kernels captured4096physicaledges/2048pulses across256batches,
four width/period combinations and256empty-read checks; eight native RTIO
resets. Expected timestamps/widths and master/satellite error checks PASS.

Two forced Genesys GTH reset cycles demonstrated link DOWN, reinitialization,
TSC acknowledgement and destination UP, followed by physical DIO PASS each.
This is finite functional recovery, not a phase/jitter/deterministic-latency
measurement or continuous BER/long-duration reliability qualification.

Both-board restoration PASS:04clock/profile/originalmux71/mode10, Genesys
normalCoreDMA/analyzer/MonInj/Ethernet192.168.2.3; leases released. No01/03/
Flash/OTP/SD/GenesysSi writes. Next consolidate a reproducible KASLI04 profile
and run remaining bounded DMA checks; active-fault tests remain separately
gated by their own idle-counter qualification.
