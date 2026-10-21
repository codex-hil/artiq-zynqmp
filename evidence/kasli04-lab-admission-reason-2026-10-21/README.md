# KASLI04 active attempt: exact timing admission rejection

Intended underflow test FAIL; diagnosis confirmed by lab callback telemetry:
ready1, first time read succeeds, now47553449704, requested47553567008,
remaining117304mu versus unchanged required1000000mu. Backend rejects at
first timing check before copying/starting DMA. Starting lead1500000mu was
consumed by1382696mu before this check. Two post-failure read-only samples
confirm armed1, active/accepted/completed/trigger/AR/RLAST0 and stable32edges.
No active underflow/AXI hold was proved; no retry or DMA reuse occurred.

Both-board restoration PASS:04clock/originalmux71/mode10,Genesys local
CoreDMA/debug/Ethernet192.168.2.3. Leases released, no01/03/Flash/OTP/SD/
GenesysSi writes. Next experiment increases initial lead to3000000mu only.
Backend minimum1ms and hardware delay2ms remain unchanged. Based on this
sample the remaining interval would be about1.62ms, but next trial must
independently prove admission/active hold/drain/native fault/TTL silence.
No timing or fault outcome is assumed from this single observation.
