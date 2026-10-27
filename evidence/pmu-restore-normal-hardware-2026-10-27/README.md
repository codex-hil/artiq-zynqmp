# Normal-only PMU restore qualification physical PASS — 2026-10-27

One shared Genesys lease80.475s, cable210383B7F02DA. Exact pinned normal
firmware baseline used; no guard, AIB request/type write or diagnostic PL image.
Stop, positive halted state, rrd -nvlist r0 exact zero dictionary, baseline PMU
download and resume all PASS in ordered seven-marker log. This physically
qualifies installed XSDB r0 response schema and changed pre-download gate.

Full normal reset/PMU/FSBL/RTIO PL/CPU load and physical TTL/CoreDMA/analyzer/
MonInj/Ethernet PASS192.168.2.3. Storage reserves allocated before bootstrap and
released before normal load; lease released at wrapper completion. No Si/SD/
flash/OTP/Kasli writes. Raw files byte-hashed; UART losslessly gzipped; generated
Python cache omitted. No forced access or retry.

This is normal-firmware context only, not guard/sleep/AIB-context restoration
qualification. Prior failed guard-context restoration remains FAIL and cause
unknown. A successful register-channel probe does not guarantee later memory
write or exclude races. No automatic unchanged diagnostic retry is admitted.
Full destructive DDR remains NOT_RUN/NOT_ADMITTED.

Next safe offline work: assess guard-context recovery obligations against this
normal control and retained failure before choosing any changed physical trial.
Keep normal baseline usable; no immediate additional reset or guard experiment.
