# Bounded candidate qualification plan

The candidate inputs and separate qualified restoration inputs are pinned in
`evidence/candidate-jtag-plan-2026-10-21/inputs.json`. A bounded JTAG hardware session passed; see the checkpoint below.
The candidate combines the second Dell PL build, clean-built CPU0/CPU1 and
rebuilt Piotr/AMD FSBL/PMU. The PS export is based on the existing verified XSA.
It has build evidence, not physical qualification or cold-boot evidence.

The wrapper `scripts/test_candidate_runtime_hw.py` implements these stages:

1. Validate every candidate and restoration digest, the remote FPGA report,
   CSR map and exact cable. Rediscover the Genesys-filtered hw_server from
   current container metadata; its IP is not persistent.
2. Acquire the nonblocking shared Genesys lease. If unavailable, return BUSY
   without UART, JTAG, network, reset or board access. Keep all test children
   under that lease, including restoration and restored network tests.
3. Perform PS system reset, new PMU/FSBL, candidate PL, matching PS initialization,
   CPU1 bridge/worker and CPU0, using the existing local runtime loader. Bound
   child execution and preserve UART, exit codes and DHCP evidence.
4. Run physical TTL loopback and standard CoreDMA/analyzer/MonInj checks, then
   Ethernet ping and byte-exact echo. Use a copied device database with the
   actual UART-reported DHCP address. Do not assume the historical IP.
5. On success, failure or child timeout, attempt restoration with the separately
   pinned old PL, old PMU/FSBL and old CPU0/CPU1 images. Repeat debug/physical
   loopback and Ethernet checks before declaring restoration PASS.
6. Write the final result while holding the lease; release after restoration.
   Overall PASS requires both candidate checks and restoration PASS. Preserve
   any restoration failure explicitly, without retries that hide its cause.

The existing helper `scripts/load_rtio_runtime.py` performs volatile loading
but does not itself provide the complete outer lease/restoration lifecycle.
Do not execute these stages piecemeal as a substitute for that wrapper.

JB1→JB2 physical loopback is required for TTL/debug checks. Do not bypass a
missing jumper or failed physical test. Do not access Kasli, Si chips, SD,
flash or OTP. This qualification does not test cold SD boot, remote DRTIO,
DDR soak, jitter or deterministic link phase. The qualified normal profile
remains unchanged until separate evidence supports a deliberate promotion.


## Reproduce and checkpoint

Offline preflight is the default:

```sh
/path/to/serial-python scripts/test_candidate_runtime_hw.py \
  --output /path/to/fresh-review
```

Hardware execution additionally requires `--execute --server CURRENT_FILTERED_SERVER
--port IDENTIFIED_GENESYS_UART --interface IDENTIFIED_LAN_INTERFACE` and a fresh
output directory. Use the existing port Python environment with pyserial;
ARTIQ debug clients use the separate shared host environment. The wrapper owns
the nonblocking Genesys lease, passes it to all children, kills the child process
group on timeout and attempts restoration. It never grants a PASS on restoration
failure. Six offline tests cover busy ownership, stale artifacts, timeout,
interrupt, candidate failure and restoration failure.

Physical checkpoint `evidence/candidate-runtime-hardware-2026-10-21`:
new PMU/FSBL, Dell PL and clean-built CPU0/CPU1 loaded; DHCP192.168.2.3,
standard CoreDMA physical TTL input/output, analyzer, MonInj and Ethernet PASS.
The debug suite runs nine DMA/analyzer scenarios, including ring wrap. Echo
checks verified1,129,210bytes over five connections; ICMP20/20. The separately
pinned old baseline was then reloaded and the same debug/Ethernet checks passed.
The shared lease covered124.298seconds and was released after restoration.

This is one JTAG qualification session. It does not establish cold SD boot,
DDR soak, remote DRTIO operation, reproducible bytes or clock phase/jitter.
The normal profile continues to select the restored old baseline. No Kasli,
Si, SD, flash or OTP was written.


## Extended candidate suite

`--extended` adds three cycles each of the existing full CoreDMA and native
exception suites on the candidate before restoration. CoreDMA covers named and
handle playback, tight64ns pulses, errors, persistence,32-slot/64KiB limits and
successful playback after a typed missing-trace error. The exception suite
checks catch/reraise/finally, overflow, uncaught kernel/RPC/RTIO errors and fresh
kernel load/RPC immediately after each error, while the RTIO counter advances.

Each extended child has a480second timeout. A final candidate debug/physical
loopback check follows the exception suite. The old baseline is then reloaded
and checked with the original debug/Ethernet suite; restoration is unchanged.
The default command retains the shorter qualification scope. Extended results
must be recorded separately from the initial124.298second session.


Extended physical checkpoint: `evidence/candidate-extended-hardware-2026-10-21`.
All3CoreDMA cycles passed (21artiq_run invocations,216pulses/432edges), including
64ns tight pulses, native DMAError reporting and successful subsequent playback.
All3exception cycles passed (30artiq_run invocations), with RTIO counter advancing
from5,800,591,559 to8,264,718,883 across catch/recovery checks. Candidate post-error
physical debug/Ethernet checks and separate old-baseline restoration checks also
passed. Lease held174.637seconds and released afterward; DHCP192.168.2.3.
Cold boot and the other excluded qualification areas remain untested here.
