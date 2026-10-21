# KASLI04 → Genesys laboratory checkpoint

Board identity: KASLI04 DNA `0x006c440674704854`, USB topology `1-11.1`,
UART channel C. SFP0 connects to the host switch; SFP1 connects to Genesys.
Genesys cable serial `210383B7F02DA`, JB1→JB2 loopback. KASLI04 has its EEM
mux0x70 physically removed; only clock mux0x71 is accessed. The opt-in source
preparation overlay preserves all remaining clock ACK/identity checks.

The verified laboratory path supports standard ARTIQ kernels, management,
remote TTL input/output, native distributed CoreDMA, repeated playback,
replacement/erase/reupload and two-packet uploads. Stability captured4096edges;
two forced GTH resets recovered through new TSC ACK and physical DIO.

This is a direct-destination1 laboratory satellite, not a complete upstream
platform. Absolute phase, jitter and deterministic latency are not measured.
No maximum-capacity/sustained-throughput proof. A separate controlled active
underflow test now passes; it requires the dedicated laboratory PL/firmware
and forbids DMA reuse until full restoration.

## Review without hardware access

Use a fresh output directory and the prepared artifact tree:

```sh
make review-drtio-qualified   DRTIO_PROFILE=diagnostics/drtio/profiles/kasli04-genesys-native-dma.json   O=/srv/codex-hil-data/artiq-zynqmp/build/my-kasli04-review
```

This validates pinned hashes/proofs, writes the resolved command and observer
configuration, then runs wrapper preflight. It does not acquire a hardware
lease or touch a device. Large build artifacts/toolchains are required; the
repository alone does not install them. Existing prepared builds and hashes
are listed in the profile. A changed artifact requires review/requalification.

## Execute the already qualified basic DMA scenario

Read `/home/codex-hil/docs/pqc-coordination.md` first. Confirm current board
allocation, physical connections, and the Genesys-filtered JTAG server endpoint.
The recorded container IP is not persistent. Do not substitute another board.
Then use a fresh output directory:

```sh
make test-hw-drtio-qualified   DRTIO_PROFILE=diagnostics/drtio/profiles/kasli04-genesys-native-dma.json   O=/srv/codex-hil-data/artiq-zynqmp/build/my-kasli04-run
```

The parent wrapper acquires only shared KASLI04+Genesys locks, sorted and
nonblocking, verifies DNA/UART and idle retained mode10 before loading SRAM.
It bounds TCP readiness at both initial boot and clock-switch restart, then
runs management/counter, AUX/TSC/reset/DIO and basic native DMA. Restore checks
cover KASLI04 clock/profile/PLL/originalmux71/mode10 and Genesys local
CoreDMA/analyzer/MonInj/Ethernet. Flash/OTP/SD are never written. Keep leases
until restoration; do not launch a second UART/network client alongside it.

Schema2 is restricted to this KASLI04 basic DMA scenario. Historical schema1
retains its catch/cursor requirements. This new profile has passed offline
review; individual underlying hardware scenarios passed with the same pinned
artifacts. Execution through this profile entry point passed physically; see
`evidence/kasli04-profile-hardware-2026-10-21/review.json`.

Evidence: `evidence/kasli04-{external-idle,native-ddma,ddma-lifecycle,ddma-fragment,link-stability}-2026-10-21`.
Long fragmented lifecycle also passed: three two-packet uploads and nine
plays,522physicaledges; see `evidence/kasli04-ddma-long-lifecycle-2026-10-21`.
Next validation: native DMA error reporting/recovery and separately admitted
active-delay fault tests.


## Controlled active-underflow checkpoint

`evidence/kasli04-active-underflow-2026-10-21` records one physical PASS:
backend start admitted, one2ms AXI read hold during active DMA, raw underflow
matched to kernel RTIOUnderflow, five AXI reads/completions drained and no
new TTL edges. Post-fault DMA remains blocked until outer restoration.
The ordinary profile does not enable this lab path. Reproduction requires
exact dedicated firmware/PL, the matching new lab-idle proof and the bounded
parent arm handshake; never add an arm command to an ordinary experiment.
