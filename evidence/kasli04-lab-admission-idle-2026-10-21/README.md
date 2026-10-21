# New admission-telemetry firmware: physical lab idle qualification PASS

Rebuilt lab firmware with callback admission tracing passed external TSC/
reset/DIO and two read-only idle samples. Ready1/epoch1; active/pending/
armed/holding/trigger/rejected/fault/raw/accepted/completed/AR/RLAST all0;
output edges32 stable. No delay arm or DMA playback issued. Exact firmware
hash is now bound to this physical idle proof; older lab proof is not used.

Both-board restoration PASS under sorted04+Genesys leases:04clock/original
mux71/mode10,Genesys localCoreDMA/debug/Ethernet192.168.2.3. Leases released,
no01/03/Flash/OTP/SD/GenesysSi writes. Next one separately admitted active
trial with this exact proof to identify original admission rejection; no
margin reduction or reuse of faulted/armed DMA before full restoration.
