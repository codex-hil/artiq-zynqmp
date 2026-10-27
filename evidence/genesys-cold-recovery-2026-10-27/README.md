# Normal runtime recovery after user reboot — 2026-10-27

User reported reboot completed. One shared Genesys lease87.214s covered UART,
PS reset/PMU+FSBL/local PL/CPU load, RTIO debug and Ethernet tests. Exact normal
artifacts verified using retained runtime-inputs manifest. No diagnostic guard or
AIB experiment run. Current normal runtime192.168.2.3 recovered PASS.

PMU ELF download succeeded; previous MicroBlaze data-register error did not recur.
Physical TTL/CoreDMA/analyzer/MonInj and Ethernet tests PASS. Real block reserves
held during recovery and released on context exit; lease released. Result's
HELD_UNTIL_COMPLETION label describes held interval, not a currently held reserve.
No Si/SD/flash/OTP/Kasli or AIB policy changes. Cold reboot itself was user-reported,
not independently measured as POR. Earlier restoration FAIL remains unchanged.
Root cause of debugger failure remains unknown; recovery does not qualify an
unchanged guard retry or full destructive DDR test.

Raw files byte-hashed; UART losslessly gzipped; generated Python cache excluded.
Next safe offline work: review restoration failure/candidate interaction before
any further guard experiment. DDR NOT_ADMITTED; normal baseline now usable.
