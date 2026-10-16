# KASLI03 master handoff

Accepted 2026-10-13 from rng-rpi `kasli/HANDOFF_KASLI03_ARTIQ.md`.
Read that handoff before deployment. User reports the Kasli loopback removed
and an SFP connection to Genesys attached. Exact downstream Kasli port awaits
operator confirmation; no remote link claim follows from this handoff.

Read-only identification PASS under all three shared Kasli locks:
DNA `0x0048458a64b04854`, XC7A100T, USB001:077, topology1-6.2.
UART channelC by-path `pci-0000:00:14.0-usb-0:6.2:1.2-port0`.
Evidence copied to `evidence/kasli03-handoff-2026-10-13/`.
No SRAM, flash or clock-profile modification performed during takeover.
Locks were released after identification.

## Image preparation

Use `kasli-v1.1-master.json`, master role, RTIO125MHz/DRTIO2.5Gb/s,
no EEM peripherals, WRPLL disabled. Preserve EEM9/10 high-Z. This is a
separate build from the earlier v2.1 image: never load that earlier image
onto this board. ARTIQ source remains pinned at486e8f897547d282d46a02c30463449c21e30cfe.

The common build script accepts `KASLI_CONFIG=/absolute/path/to/config.json`
and reads its variant rather than assuming v2.1. The current build output is
`/srv/codex-hil-data/artiq-zynqmp/build/kasli-v1.1-master-2026-10-13/`.
Build started, completion/timing acceptance pending. No hardware lock is held
for the offline build.

## Deployment gates

- Review routed setup/hold/pulse timing, DRC, part and image/firmware hashes.
- Establish a RAM-only firmware path. Upstream bootloader attempts flash boot
  before network boot. Do not run unknown previous flash firmware; prepare a
  controlled netboot-only bootloader overlay or verified RAM loader first.
  Keep original sources and flash storage unchanged.
- Confirm current USB topology and exact DNA immediately before SRAM loading.
- Acquire all required shared Kasli locks nonblocking. A cross-board session
  must also hold the Genesys lock, acquired in lexical order, for the whole
  load/test/restoration period, including both UARTs and network traffic.
- Use the handed-over checked SRAM restoration procedure. Si5324 initialization
  by ARTIQ is volatile but must be recorded and its restoration addressed.
- Use unique network identity. The default master device_db IP is only a
  placeholder, not board configuration or evidence of connectivity.

Genesys currently has a validated local core and laboratory internal-loopback
AUX services. The extracted real satellite backend has seven simulation tests
and generated HDL; a routed external satellite transport/reset/CDC integration
is still pending. Do not claim remote discovery, TSC synchronization or remote
TTL execution from the current state.

## Build checkpoint

Original v1.1 build completed: bitstream/bootloader/runtime PASS. Setup
WNS0.001ns, hold WHS0.061ns, pulse slack0.264ns; no violating endpoints.
Very small positive setup slack and inherited external timing warnings require
hardware qualification. Bit SHA256322910c4441297ad4757f0cd33bcf3d3bdf11e6f6e657394c28ba7b7d0dce7b4.
This flash-first image has not been selected for deployment.

`prepare_netboot_source.py` creates a separate detached worktree at the exact
pinned upstream revision and checked boot/network overlays. It disables the
flash-boot branch, fixes unique lab MAC02:4b:03:48:48:54, selects DHCP and
removes inherited static addresses/routes. No EEPROM/flash writes are introduced.
The reviewable overlay is `kasli03-netboot.patch`; the original source remains
unchanged. Upstream volatile clock initialization is retained, not yet tested
on this board.

Netboot-only build is running in `build/kasli03-netboot-2026-10-13` on the data
volume. Initial overlay compilation found a shadowed untyped None; this was
corrected before restarting the build. Firmware/bitstream acceptance pending.

## Bounded bootloader-only acceptance

`scripts/test_kasli03_netboot_hw.py` is prepared but NOT_RUN. It requires a
reviewed netboot-only qualification JSON plus exact bit SHA and passing timing.
`--dry-run` checks files only. Actual execution holds all three shared Kasli
locks; verifies USB topology and DNA before SRAM loading; captures exclusive
UART; requires bootloader CRC, SDRAM initialization/memory test, disabled flash
boot and the unique DHCP identity. It does not upload runtime or touch Genesys,
so no Si5324 runtime initialization is performed by this stage.

After any programming attempt it restores the handed-over full-checker image
with its existing guarded loader and checks UARTBone identity/EEMenable0/
GTPcontrol0/SFPTXdisable7 with bounded reads before releasing the locks.
This is not remote DRTIO or even runtime acceptance. Runtime clock changes need
a separate restoration plan before that later test.

The interrupted foreground build was restarted as the user systemd service
`artiq-kasli03-netboot-20261013.service`; check ActiveState/ExecMainStatus and
`systemd-build.log` in the netboot output directory. It runs a frozen build
script snapshot, holds no hardware locks and performs no device operations.

## Bootloader networking correction

Source inspection confirmed the upstream bootloader does **not** start a DHCP
client. `IPv4=use_dhcp` in its console is the selected configuration policy,
not a lease or proof of IPv4 connectivity. The runtime has its own networking.
The netboot-only image can listen on IPv6 link-local
`fe80::4b:3ff:fe48:4854` (derived from the forced lab MAC), TCP4269; the host
must provide the actual switch-facing interface scope. No IPv6 connection
has been tested yet. A separate static IPv4 profile would require a rebuild.
The startup wrapper checks `Waiting for connections...` but reports DHCP
as not implemented and does not claim network acceptance from that console.

The upstream wire format is `F`, four-byte big-endian runtime binary length,
raw runtime.bin payload, `OK`, then `B` to request execution. runtime.fbi has
an extra header and is not the raw netboot payload. Do not send runtime until
its clock configuration/restoration and shared hardware lease are addressed.

`qualify_netboot_build.py --build BUILD --source SOURCE --output JSON` checks
the exact upstream revision and reviewed overlay, selected bootloader path,
v1.1 master config/part, timing summary/violating endpoints, DRC severity,
completion marker and all firmware/bitstream hashes before issuing the
qualification required by the hardware wrapper. Negative control using the
completed original flash-first build was correctly rejected for selecting the
wrong bootloader source. Positive netboot qualification awaits routing.

## Failed deployment and correction — 2026-10-13

The first netboot-only qualification was insufficient and is **withdrawn**.
The built bootloader was not embedded: standard Kasli CPU reset points at flash
0x400000. SRAM loading therefore ran the existing 2024 MiSoC bootloader, passed
its DDR tests, then started old ARTIQ8 `VOR2309003` from flash. That runtime
configured Si5324 internal125MHz and reported lock/reboot. No flash programming
commands were issued, but flash content was not re-read after this test.

The bounded test correctly failed its required netboot UART checks. Its finally
path restored full-checker SRAM and verified identity/EEM0/GTP0/SFPdisable7.
Exact original Si5324 registers were not captured/restored; do not describe the
clock profile as unchanged. Raw UART and results are in
`evidence/kasli03-netboot-hardware-2026-10-13/`.

Corrected source is the separate `work/kasli03-bram-netboot` worktree. Build uses
`KASLI_ROM_SIZE=131072`: MiSoC resets CPU at zero and removes the SPI-flash core.
ARTIQ's builder needs a local initialization hook because the generic MiSoC
hook loads `software/bios/bios.bin`, while ARTIQ builds `bootloader.bin`.
The checked overlay initializes ROM words from the compiled bootloader and
records reset address/ROM size/hash in `bram-boot.json`. Flash boot code is
removed from this no-flash laboratory image, not merely hidden behind a branch.
Qualification and the hardware wrapper now require this embedded-ROM evidence.
The old image negative control is rejected for lacking it.

Corrected build is running as `artiq-kasli03-bram-netboot-20261013.service`,
output `build/kasli03-bram-netboot-2026-10-13`. No corrected image has been loaded.
Next physical test remains bootloader-only; runtime clock restoration is a
separate acceptance step. Original sources and prior artifact/log trees remain.

The first integrated-ROM attempt exposed upstream runtime assumptions:
unconditional SPI-flash imports/reload/FLASH_BOOT_ADDRESS do not compile when
MiSoC omits the flash core. This is not solved by claiming a complete runtime.
For the bounded next test, the BRAM builder intentionally compiles only the
bootloader; the qualifier marks bootloader-only scope and does not require
runtime artifacts. Runtime support without flash remains a separate offline
implementation step. Corrected firmware and actual ROM initialization PASS;
`bram-boot.json` generated. FPGA routing remains pending.

## Embedded bootloader hardware PASS

Routed BRAM image SHA4fb33ce837d29cfe727e97c6e0e5cd86f761b7b60c8800c26eb35a5891a99715,
WNS0.092/WHS0.051/pulse0.264ns. Qualifier now also compares the complete
`mem.init` word sequence to compiled bootloader bytes and checks generated HDL
reset-zero and ROM initialization wiring. Positive qualification PASS.

Physical SRAM boot PASS: 2026 upstream bootloader, CRC, DDR initialization and
memory test, disabled flash boot, correct forced MAC and network listener startup.
No runtime uploaded, old flash runtime absent from UART, no Si5324 setup observed.
First host assertion falsely rejected hyphen-separated MAC; corrected to match
actual upstream display and repeated full load/test/restoration PASS.
Both sessions restored full-checker and CSR baseline under all three shared
Kasli locks. Raw evidence in `evidence/kasli03-bram-netboot-hardware-2026-10-13`.
Network TCP connectivity and remote DRTIO remain NOT_RUN.

## Flash-free runtime compile PASS

`prepare_flashfree_runtime.py` creates a separate worktree from the reviewed
BRAM overlay, enables runtime compilation, and guards upstream SPI-dependent
imports/functions with has_spiflash. In no-flash builds, management flash/reboot
return Error and panic halts; upstream configuration returns NoFlash. Flash
builds retain their original behavior. The reviewable patch is
`kasli03-flashfree-runtime.patch`. First overlay shape check caught duplicate
local/remote function names; the corrected script changes only local handlers.

Full bootloader/ksupport/runtime compile PASS in
`build/kasli03-flashfree-runtime-2026-10-13/generated-fixed`. Generated mem.rs,
csr.rs and regions.ld are byte-identical to the physically tested BRAM image.
Runtime hardware NOT_RUN. Evidence kasli03-flashfree-runtime-build-2026-10-13.json.
Next: establish host-scoped IPv6 netboot connectivity and a bounded runtime
clock-profile capture/restoration plan before firmware execution.

## IPv6 netboot connectivity acceptance

The same bounded wrapper now accepts `--network-interface enp1s0`. It checks
that the host has a usable IPv6 link-local address before touching hardware.
Under the Kasli lease, after boot evidence it opens TCP4269, sends only an
unknown command and a boot request without firmware, requires connection close
and matching UART rejection evidence, then opens a fresh third connection.
It also checks the IPv6 neighbor MAC is02:4b:03:48:48:54. No firmware download
or execution is performed. The normal guarded diagnostic restoration remains
in finally. This network extension is prepared, physical test NOT_RUN.

At preparation time enp1s0 had no IPv6 link-local address and sudo needed a
password. Operator command requested:

```sh
sudo ip -6 addr add fe80::c0de:3/64 dev enp1s0
```

This temporary host address does not replace IPv4. No privilege workaround
or host network mutation was performed by the agent. Once available, run the
bounded wrapper with the existing reviewed BRAM qualification and exact SHA.

## Physical IPv6 netboot network PASS

Operator added host link-local fe80::c0de:3/64 on enp1s0. Bounded wrapper with
`--network-interface enp1s0` PASS: three TCP4269 connections, unknown-command
rejection, boot-without-firmware rejection and fresh listener recovery. UART
confirms each command rejection; neighbor MAC02:4b:03:48:48:54 matches KASLI03.
No runtime bytes uploaded or executed. Shared three-Kasli lease covered the
whole SRAM/UART/network/restoration session; full-checker CSR baseline restored
PASS. No Genesys access or observed Si5324 setup. Raw evidence:
`evidence/kasli03-netboot-network-2026-10-13`.

The operator's temporary host IPv6 address remains in place for subsequent
netboot tests. Next useful step is a bounded RAM download without the B command,
then runtime execution only with clock/reset behavior accounted for. Upstream
runtime may initiate a sys-clock switch/reboot and return to the BRAM loader;
that may require a second firmware download, not a flash boot.

## Physical RAM firmware download PASS

Bounded wrapper `--download-runtime /path/runtime.bin --runtime-sha256 SHA`
with the IPv6 interface checks the reviewed source hash/maximum4MiB size before
hardware. It sends F + big-endian length + chunks + OK, waits for the upstream
UART completion and never sends B. Physical test PASS for1752788 bytes,
SHA4799375ac6490807578b147efa91ac84dc2154c0b4eb640c35dda15147d4bdef.
UART confirms Received firmware load command/Firmware successfully downloaded.
No ARTIQ runtime execution or Si5324 setup observed. RAM readback/checksum is
NOT_RUN; completion does not establish byte-exact stored memory independently.

Boot/DDR and TCP negative/recovery checks repeated PASS; shared locks covered
whole test/restoration. Full-checker CSR restoration PASS. Evidence
`evidence/kasli03-netboot-download-2026-10-13`.
The connection is closed afterward; upstream clears its firmware_downloaded
flag on disconnect. Runtime execution must download and issue B on the same
connection in a later separately bounded session. Next preparation is a clock
snapshot and safe restoration plan, then controlled runtime execution.

## Read-only clock snapshot

Physical snapshot acquisition PASS:27 Si5324 registers selected from the actual
retained driver read/write addresses, two identical readings each, expected
ID0182 and PLLlocked. Seven transient address/offset NACKs required bounded
retries, so I2C reliability remains PARTIAL. Three shared Kasli locks held for
41.551s, no clock data/FPGA/flash write; mux70=0/71=8 and prior bus CSR restored.
Raw evidence: `evidence/kasli03-clock-snapshot-2026-10-13`.

Decoded dividers exactly match current upstream Int125: N1HS10, NC1/2LS4,
N2HS10, N2LS19972, N31/N324565, BWSEL4, FREE_RUN1, selected CKIN2.
This comparison uses the retained driver encoding and runtime settings; it is
not an independent frequency/jitter measurement or validation of a restoration
sequence. Do not blindly replay readonly/status/ICAL registers. Snapshot covers
registers touched/read by that driver, not every Si5324 register or factory state.

Next: account for runtime Si5324 hard-reset/sys-clock switch behavior and
validate bounded restoration against this baseline before full execution.

## Clock/reset restoration plan — 2026-10-14

`plan_kasli03_clock_restore.py` validates snapshot DNA, duplicate reads, exact
driver hash and generated Rust cfg. Actual build selects **si5324_soft_reset**;
previous generic references to runtime hard reset do not apply to this build.
The checked plan contains23 configuration registers, excluding status/product
ID and register136 command bits. Saved reset/ICAL bits must never be replayed.
If configuration changes, restoration requires a deliberate fresh calibration,
readback/lock/output-frequency validation and mux/bus restoration.
This is an offline plan, not a validated hardware recovery sequence.
Unstable-read negative control rejected with no plan output.

Runtime first setup may switch sys clock and reset CPU to BRAM loader; second
same-connection firmware download/B after loader recovery should skip setup
via switch_done. This flow remains physically NOT_RUN.
Runtime enables downstream TX, so the user's Genesys connection requires the
Genesys lock as well as all three Kasli locks, acquired lexically/nonblocking
and held through tests/restoration. No independent runtime attempt is allowed
under only a Kasli lease while Genesys is in use.
Plan evidence: `evidence/kasli03-clock-restore-plan-2026-10-14.json`.

## USB relocation and fresh timing comparison — 2026-10-15

Verified DNA0048458a64b04854 now at topology1-2.4.1, USB001:019, UART channelC
`/dev/serial/by-path/pci-0000:00:14.0-usb-0:2.4.1:1.2-port0`.
Capture/netboot wrappers accept explicit `--usb-topology` and `--uart` and
verify UART belongs to that USB interface before opening it. Historical default
paths stay unchanged; pass the current confirmed location explicitly.

Fresh ordered A/B: original54 reads/13 retried NACKs, settled54 reads/zero;
values identical and PLLlocked, routing restored. No programming/clock changes.
See evidence/kasli03-clock-ab-2026-10-15. Restorable clock profile validation
and runtime execution remain pending; this test only characterizes reads.

## Volatile profile reset/restore hardware PASS — 2026-10-15

Capture wrapper `--settled-timing --restore-plan PLAN` now optionally performs
an explicitly volatile test after comparing a fresh repeated snapshot with the
reviewed baseline. It requires EEMenable0/GTPcontrol0/SFPdisable7 before mutation.
No FPGA/flash/OTP/runtime/Genesys operations. Shared three-Kasli lease149.249s.

Physical PASS: expected reset-value NACK,23 configuration writes, fresh ICAL,
command bits settled/PLLlocked, exact23-register readback and product ID0182.
No ordinary transfer retries or NACKs. One bounded recovery attempt is available
if a transfer fails; it never repeats the reset. Two offline controls verify
normal restore/reset-NACK acceptance and bounded failure on configuration NACK.

Three counter/host-time samples were approximately125.51/125.54/125.52MHz,
inside the deliberately coarse125MHz ±1% diagnostic tolerance. This detects
wrong nominal clocks; it is not a calibrated frequency/ppm/jitter measurement.
Mux and bus CSR restored; snapshot confirms original config values, not every
reserved register or analog phase. Evidence kasli03-clock-restore-2026-10-15.
Next controlled runtime execution must hold Genesys plus all Kasli leases,
include post-test diagnostic/profile restoration and handle the clock-switch
reboot/re-download flow. SFP physical port mapping still needs confirmation
before claiming external link behavior.

## ARTIQ10 runtime RAM startup hardware PASS — 2026-10-15

The bounded wrapper's explicit `--execute-runtime` requires reviewed payload
hash plus clock baseline/plan/physical restoration validation. It acquires
Genesys and all three Kasli locks lexically/nonblocking for the whole session,
including UART/TCP, downstream TX activation and diagnostic/clock restoration.
Genesys is leased because of the external cable; its FPGA/configuration is not
programmed. Current host interface is enp2s0 with native IPv6 link-local.

Physical PASS: first upload/B runs current ARTIQ10, soft-reset/PLL setup and
sys-clock switch return CPU to BRAM loader. Second upload/B skips clock setup
via switch_done. UART shows matching software/gateware identifiers,
management interface active and accepting network sessions. No flash command
or original flash runtime. No standard management-client transaction, kernel
experiment, remote AUX/discovery/TSC/TTL or external DRTIO acceptance yet.
Two offline controls verify reboot/re-download handling and panic rejection.

Finally full-checker/disabled outputs restored PASS, then reviewed23-register
clock profile reset/restored/calibrated, readback/PLL/nominal125MHz ±1% PASS,
mux/bus restored. These are intentional volatile Si writes, no flash/OTP.
Evidence: `evidence/kasli03-runtime-startup-2026-10-15`.
Reproducer: netboot wrapper with --execute-runtime, --download-runtime,
--runtime-sha256, --clock-plan, --clock-baseline, --clock-validation plus
current explicit USB/UART/interface and reviewed BRAM artifact arguments.
Next: bounded standard management client queries and a simple local kernel.

## Standard management-client hardware PASS

Bounded wrapper `--management-client` requires --execute-runtime and invokes
unmodified installed `artiq_coremgmt -D fe80::4b:3ff:fe48:4854%enp2s0 log`.
Two independent connections PASS, returning1909/2000 characters with matching
runtime identity and active management/session services. Parent retains Genesys
and three Kasli locks during child network clients and final diagnostic/profile
restoration, both PASS. No flash/OTP. Evidence kasli03-management-2026-10-15.

`examples/kasli_counter_probe.py` compiles successfully for generated Kasli1.1
rv32ima device database; ELF32/RISC-V verified. It reads advancing RTIO counter,
waits on the local timeline and tests synchronous scalar RPC return, without
TTL writes. Hardware kernel execution NOT_RUN. Global delay did not resolve
in this NAC3 context; explicit core.delay compiles. Generated device_db has a
placeholder IPv4 address; physical execution must supply scoped actual host
and disable unstarted optional analyzer proxy. Next: run this experiment in
the same bounded cross-board session before diagnostic/profile restoration.

## Standard local kernel/RPC hardware PASS — 2026-10-15

Run the reviewed netboot wrapper with all runtime/management arguments above
and `--counter-experiment`. It supplies the actual scoped core host, rv32ima
and1ns machine unit, disables the optional analyzer proxy and invokes standard
artiq_run twice on examples/kasli_counter_probe.py. Each invocation compiles,
uploads and executes a fresh kernel, waits at least1ms on the RTIO timeline,
then checks synchronous scalar RPC return0x12345678. The host also requires
the printed before/after values and minimum1000000mu interval.

Physical runs PASS:7079654360→7080778752 and7566664016→7567788792mu.
Two management connections and final diagnostic/clock restoration also PASS.
Shared Genesys+three Kasli locks cover the complete window. No TTL writes,
Genesys configuration, flash or OTP writes. Evidence:
`evidence/kasli03-counter-2026-10-15`. Earlier NOT_RUN notes above are historical.
This does not establish external DRTIO synchronization or remote TTL operation.


## Pinned NAC3 DMA tuple ABI and native DDMA (2026-10-16)

The standard native-DDMA experiment initially panicked in Kasli ksupport's
DMA pointer-alignment assertion. The compiled NAC3 caller allocates24 bytes
and reads address at16, while upstream ksupport's legacy tuple had no8-byte
ObjectHeader and returned address at8. Keep the alignment assertion. Prepare
an isolated RAM-only source with the optional ABI overlay:

```sh
python3 diagnostics/kasli-master/prepare_flashfree_runtime.py \
  --source /srv/codex-hil-data/artiq-zynqmp/reference/artiq \
  --output /srv/codex-hil-data/artiq-zynqmp/work/kasli03-bram-runtime-dma-abi \
  --nac3-dma-abi
```

Use a fresh worktree path when reproducing; the script refuses overwrites.
The firmware generation command must use `--integrated-rom-size 131072`,
matching the qualified BRAM bit. An initial65536-byte attempt overflowed ROM;
the corrected128KiB build passed. The complete offline build invocation is
recorded in `evidence/kasli03-dma-abi-build-2026-10-16/build.sh`, run under
`tools-env.nix` with ARTIQ_SOURCE set to that isolated worktree. It does not
invoke Vivado. Generated mem.rs/csr.rs/regions.ld must all match the existing
qualified bitstream before RAM download; recorded hashes are in abi-headers.json.

Runtime SHA256 f0b53c4cc100951258422bb1bb6e617348cda8eacc0eacc10a09e71968d79d4b
passed guarded management/counter/reset/DIO and native distributed CoreDMA
upload/playback/status/erase plus physical8-edge loopback. Both boards restored
PASS. Evidence `kasli03-native-ddma-fixedabi-hardware-2026-10-16`. Use the
existing all-four-board-lease wrapper and preserve its snapshot/DIO prerequisite;
never flash this laboratory runtime. Repetition/abort/general RTIO remain pending.
