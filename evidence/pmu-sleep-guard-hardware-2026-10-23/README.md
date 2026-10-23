# Physical sleep guard capture and restoration — 2026-10-23

One parent-owned Genesys lease, cable 210383B7F02DA, duration143.994s.
Candidate PASS and restoration PASS. Four coherent nonce-bound guard records;
MSR before0x80000106, after0x80000104: only IE(bit1) cleared. State2,
generation2, sequence1, ACK0, unresolved0x7f, kind2. No RAM timeout or retry.
Exact changed sleep image SHA256:
7a82b8f2ac5beb2bff4cafaa3767b888c09461a7c66371f632332f7bd66f51c4.
Fresh manifest: ../pmu-sleep-guard-integration-2026-10-23/inputs.json.

Explicit PMU debugger halt/baseline download/resume PASS; full normal reset/load,
physical TTL/CoreDMA/analyzer wrap/MonInj and Ethernet restoration PASS192.168.2.3.
Two filesystems each reserved768MiB real blocks and released them before restore.
Wrapper completed and released lease. No Si/SD/flash/OTP/Kasli changes.

This proves sampled IE-cleared guard publication and successful external capture,
consistent with the documented PMU RAM sleep arbitration requirement. It does
not measure continuous sleep residency or terminal PC, exclude ROM/NMI/error
paths, establish all-core/future-wakeup exclusion or exclusive DDR ownership.
Full destructive DDR remains NOT_RUN/NOT_ADMITTED. Previous nop-guard FAIL is
preserved; this successful changed trial does not rewrite its status.

Raw file sizes/hashes in raw-inventory.json; UART compressed losslessly. Binary
analyzer captures are marked binary by repository attributes. Verify staged Git
blobs against raw inventory before publishing. Next offline: enumerate remaining
DDR exclusion obligations and identify the next independently provable boundary;
do not repeat successful unchanged hardware capture.
