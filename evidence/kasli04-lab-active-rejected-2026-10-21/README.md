# KASLI04 active-fault attempt: playback admission rejected

Overall FAIL for the intended active-underflow qualification. Exact lab idle
proof/artifacts/host overlay admitted, fresh idle samples PASS. Valid34-byte
trace upload ACK; one guarded UART arm250000cycles ACK. Native playback
request NACK, kernel raised DMAError (expected test catches RTIOUnderflow
only), so no active-underflow success marker. No active/drain/completion
evidence established; do not infer that fault injection actually triggered.

No retry/reset/erase/reuse of DMA attempted after failure. Read-only generic
startup status confirms correct PL/reset0/RXup1 but does not diagnose DMA
admission. Exact admission failure cause remains unknown; minimum1ms future
start margin versus requested1.5ms is a hypothesis, not established cause.

Both-board restoration PASS:04clock/originalmux71/mode10,Genesys local
CoreDMA/debug/Ethernet192.168.2.3; leases released. No01/03/Flash/OTP/SD/
GenesysSi writes. Next offline instrument precise admission decision and
read-only post-rejection counters before any new active attempt. Preserve
all admission checks; do not lower margins or reuse armed DMA to force PASS.
