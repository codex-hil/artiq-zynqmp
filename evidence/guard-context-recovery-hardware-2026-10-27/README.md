# Guard-context recovery with r0 gate physical PASS — 2026-10-27

ONE physical attempt, shared Genesys lease145.512s. Exact vector-v1 guard and
no-master PL, no post-guard AIB capture. Guard record PASS. Positive PMU stop,
r0zero dictionary, baseline firmware download and resume PASS; all seven stage
markers occur exactly once in order. Full normal reset/load and physical TTL/
CoreDMA/analyzer/MonInj/Ethernet restoration PASS192.168.2.3. Lease released.
TwoFS768MiB reserves allocated/released before restoration. No Si/SD/flash/OTP/
Kasli/remap/AIB policy changes, forced access or physical retry.

Initial invocation was refused before hardware by storage reserve requirement.
Own completed Kasli03 BRAM netboot build was copied/hash-verified to root disk,
1380entries855401331logicalbytes, original path preserved by symlink; no Kasli HW.
Fresh v2 output used. Thresholds unchanged, original refusal preserved separately.

This proves the changed recovery sequence worked in this no-AIB guard context.
It does not explain the earlier post-AIB download failure, prove AIB causation,
or guarantee future memory writes after r0probe. Previous FAIL stays unchanged.
No unchanged physical repeat is selected. Full DDR remains NOT_RUN/NOT_ADMITTED.

Next safe offline: classify existing AIB REQ/ACK00c00000 and TYPE19cf000f by
specific instance and boot-source initialization; determine master coverage and
control dependencies without new isolation writes or another guard experiment.
Raw capture hashes checked byte-exact before publication; UART gzip lossless.
