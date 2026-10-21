# KASLI04/Genesys laboratory DMA idle counters PASS

Separate hash-qualified delay/metrics PL and lab firmware, admitted only in
explicit idle mode. External TSC/reset/DIO passed. Two read-only UART samples
reported ready1/epoch1, DMA active/pending/armed/holding/fault/raw all0, no
accepted/completed/trigger/rejected transactions, AXI AR/RLAST0, output-edge
count32 unchanged. No delay-arm command or DMA playback was issued.

Both-board restoration PASS under sorted04+Genesys leases:04clock/original
mux71/mode10 and Genesys localCoreDMA/debug/Ethernet192.168.2.3. Leases
released; no01/03/Flash/OTP/SD/GenesysSi writes. This is required prior idle
qualification, not active-underflow proof. An active test must separately
validate this exact PL/firmware proof and host overlay, arm once through
the bounded handshake, preserve native error evidence and forbid DMA reuse
after fault until full restoration.
