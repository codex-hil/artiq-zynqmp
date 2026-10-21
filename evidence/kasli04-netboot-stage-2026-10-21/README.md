# KASLI04 netboot passes; subsequent first TCP connect times out

Two bounded, distinct trials with exact DNA and retained-mode10 checks:

- Network/download-only trial PASS: three TCP negative/recovery connections,
  correct neighbor MAC,1756088-byte RAM firmware download acknowledged.
  No boot command, runtime NOT_RUN, RAM readback NOT_RUN.
- Subsequent runtime-intended trial FAIL at `negative-0:connect`, before
  any command/payload/runtime. Error-time own IPv6 neighbor state DELAY.

Both temporary diagnostic and retained mode10 restorations PASS, all leases
released. No clock-profile/flash/OTP/SD/Genesys/other-Kasli access.

Network reachability is intermittent immediately after FPGA programming;
no root cause established. A link/switch startup delay is a hypothesis.
Next bounded readiness test should record time from programming/boot to
first successful connection, retaining all limits and restoration. Do not
claim runtime/DRTIO success or change switch configuration based on this.
