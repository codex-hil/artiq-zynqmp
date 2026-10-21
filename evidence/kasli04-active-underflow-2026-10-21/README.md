# KASLI04 → Genesys active native DMA underflow PASS

Exact new lab firmware/PL and physical idle proof admitted. One guarded
250000cycle/2ms AXI read-delay arm; kernel schedules3ms ahead, backend1ms
minimum unchanged. Native playback admitted, hardware active+holding and
one trigger observed. Completion raw4/channel0/timestamp51188039120 matches
kernel-caught RTIOUnderflow and upstream AUX underflow status. Independent
metrics AR5/RLAST5 drained, output-edge count32 unchanged. Accepted/completed
1/1; postfault two stable samples ready0/epoch1/active0/pending1/armed0/
holding0/faulted1/raw4. No postfault DMA reset/erase/retry/reuse.

Both-board restoration PASS under sorted04+Genesys leases:04clock/original
mux71/mode10; Genesys localCoreDMA/analyzer/MonInj/Ethernet192.168.2.3. Leases
released; no01/03/Flash/OTP/SD/GenesysSi writes. One controlled active-fault
proof only: not random faults, arbitrary recovery, maximum throughput or
phase/jitter qualification. Next consolidate lab reproducer/status and
remaining integration gaps; normal pinned DMA profile remains unchanged.
