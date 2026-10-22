# Bounded base-SPD reader preparation

Status: **offline orchestration controls PASS; AMD adapter candidate compiles; vendor-ISR integration and hardware NOT_RUN**.
No deployment command is provided yet. This does not qualify DDR.

`spd_reader.h` is transaction orchestration, not an I2C controller driver.
The candidate `spd_xiicps.h` reuses AMD XIicPs nonblocking begin/master ISR
callbacks; integration admission is still pending. The current vendor `MasterRecvPolled` calls `MasterPolledRead`, whose
receive wait has no local deadline. A caller-side deadline cannot interrupt a
blocked vendor call. Do not bind that API to these callbacks.

The caller must prove exclusive I2C1 ownership and a **known lower-page baseline**
before admission. The existing FSBL reader leaves the upper page selected; simply
calling this reader after FSBL is therefore not admitted. Page identity/state
establishment and adapter integration remain open. No unknown page is silently
assumed or called restored.

The fixed sequence is lower-page select (`0x36`, one zero byte), SPD offset zero
(`0x51`, one byte), receive128bytes, offset zero, receive128bytes, then lower-page
cleanup. No other addresses, mux operations, EEPROM data programming, bus clear,
retries or upper-page selection. Each stage has100ms budget and10000poll limit;
clock reversal/overflow fail. `tick` must receive monotonic microseconds and the
callbacks themselves must be bounded. On failure, attempt one cleanup only when
the adapter confirms both bus idle and no outstanding transfer/callback. A busy
or unknown state ends with `page_restored=0`, requiring outer recovery; never
force the bus idle. The outer lease and timeout must cover recovery/restoration.

Accept a capture only when `stopped && result == SPD_PASS && page_restored`.
Raw bytes must be retained, then CRC and independent controller geometry checked.
Matching two captures is not a CRC check or proof of physical capacity.

Host controls (fake transport, no HW):

```sh
cc -std=c11 -Wall -Wextra -Werror -fsanitize=address,undefined \
  tests/test_spd_reader.c -o /tmp/artiq-test-spd-reader
/tmp/artiq-test-spd-reader
```

Controls cover refused admission, exact addresses/lengths, equal/mismatched
captures, each of six begin/completion failures, cleanup failure, elapsed/poll
limits and busy-bus cleanup refusal. They do not test an AMD driver or timing on
silicon. Next audit nonblocking AMD entry/handler paths, bind the callbacks,
compile against the existing BSP and test adapter failure handling before any
bounded physical acquisition with mandatory normal ARTIQ restoration.

## AMD adapter candidate

`spd_xiicps.h` uses `XIicPs_MasterSend/MasterRecv` and manually services
`XIicPs_MasterInterruptHandler`; no concurrent GIC dispatch is permitted. Bind
requires a caller assertion of exclusive/no-GIC ownership, initialized I2C1
0xff030000, platformZynqMP, seven-bit/non-repeated-start mode and idle bus. This
assertion is a precondition, not independently verified IRQ routing. Callbacks
are replaced; controller/GIC/callback snapshot/restoration is not implemented.
No repeated bind/reuse after error/timeout before outer restoration.

Unexpected events (including completion+NACK), residual byte counts or an error
poison the adapter. While pending, active state prevents cleanup even if hardware
bus busy clears. Completion requires correct event, zero residual count and idle
bus, then disables peripheral IRQs. Outer timeout/recovery remains necessary.
Source review distinguishes the legacy Zynq FIFO-wait branch from ZynqMP. This
is not yet a complete call-graph/timing proof of the actual AMD ISR.

Host adapter controls (mocked AMD APIs; vendor ISR not executed):

```sh
cc -std=c11 -Wall -Wextra -Werror -fsanitize=address,undefined \
  -Itests/spd_stubs tests/test_spd_xiicps.c -o /tmp/artiq-test-spd-adapter
/tmp/artiq-test-spd-adapter
```

A translation unit including the adapter and calling `spd_amd_bind` compiled
with ARM GNU13.2 `aarch64-none-elf-gcc`, real qualified BSP includes, C11 and
`-Wall -Wextra -Werror`. This is compilation only, not a linked executable.
Next test the actual vendor ISR/call graph against a register model and complete
page/controller/IRQ/callback restoration before creating a physical wrapper.

## Actual AMD receive-path model

The host model now executes unmodified extracted `MasterInterruptHandler`,
`MasterIntrRead`, `MasterIntrSend` and `MasterRead` with the actual BSP macros,
replacing MMIO with a register model. It is not the complete vendor build or
full adapter integration. Send continuation is excluded; the receive path and
ZynqMP branch are exercised. Six scenarios: no event, full/partial receive,
NACK, hardware timeout and stuck RX-data-valid.

The stuck-RXDV scenario detects an attempted129th read into a128-byte receive
buffer. A host guard intercepts the attempt before the out-of-buffer store;
this is an injected model fault, not an observed physical board failure.
AMD `MasterRead` loops on RX-data-valid without checking remaining receive
count. Consequently the current adapter is **NOT admitted to hardware** even
though its API-only controls and AArch64 compilation passed. Preserve the
negative result. Next add a minimal auditable change to a copied vendor
source that bounds receive count and rejects residual RX data, then test both
original-negative and patched-positive paths. Do not edit the shared BSP or
claim a caller deadline interrupts an unbounded ISR.

```sh
python3 scripts/test_spd_vendor_receive.py \
  --bsp /srv/codex-hil-data/artiq-zynqmp/build-vivado/release-boot-firmware-2026-10-21/bsp \
  --output /tmp/FRESH-spd-vendor-model.json
```

Source/header hashes and scope are retained in
`evidence/spd-vendor-isr-model-2026-10-22/results.json`. The reported model
controls PASS includes detection of the known negative scenario; it does not
mean the vendor code passed stuck-peripheral robustness.

## Isolated AMD receive-bounds patch

`prepare_spd_vendor.py --bsp BSP --output FRESH` copies three vendor C files,
retains their hashes and emits a unified patch. Originals/shared BSP are never
modified. Exact missing/duplicate edit anchors and second application reject.
Only two functions change: `MasterRead` requires remaining bytes before reading
FIFO; master ISR adds ERROR when receive count is exhausted but RXDV remains.
The adapter must treat completion+ERROR as failure (never accept partial success).
No bus-clear/reset workaround or replacement controller driver is introduced.

```sh
python3 scripts/prepare_spd_vendor.py --bsp "$BSP" --output "$FRESH_COPY"
python3 scripts/test_spd_vendor_receive.py --bsp "$BSP" \
  --patched-root "$FRESH_COPY" --output /tmp/FRESH-patched-model.json
```

Original6-scenario negative model retained; patched7-scenario model includes
stuck RXDV and zero remaining bytes on entry, both returning ERROR without an
extra read. ASan/UBSan controls PASS. All three full copied source files compile
to AArch64 objects with actual BSP headers and `-Wall -Wextra -Werror`; not a
linked firmware. Evidence/diff/source+object hashes:
`evidence/spd-vendor-bounds-2026-10-22`. Adapter+patched ISR integration and
restoration remain untested; hardware remains NOT_ADMITTED. These bounds do not
guarantee return from a physically stalled MMIO access.

## Reader + adapter + actual AMD function integration

Eight host register-model scenarios now execute the state machine, adapter and
11extracted AMD functions, including actual MasterSend/Recv, SetupMaster, FIFO
fill, callback installation, bus-idle check and patched receive ISR path. No
mocked begin/completion APIs in this integration model. MMIO, platform response
and FIFO availability remain modeled. The model can expose a complete payload
in one ISR call; this is deliberately not a physical FIFO/timing simulation.

Two matching128-byte reads and cleanup PASS. NACK, hardware timeout, stuck RXDV
and completion+NACK poison the adapter; partial/no completion reaches bounded
deadline with active adapter refusing cleanup/reuse. Different blocks return
MISMATCH with cleanup. All8scenarios PASS with ASan/UBSan. Source-copy manifest
hashes are checked before compilation; originals remain untouched.

```sh
python3 scripts/test_spd_amd_integration.py --bsp "$BSP" \
  --patched-root "$FRESH_COPY" --output /tmp/FRESH-integration.json
```

Evidence: `evidence/spd-amd-integration-2026-10-22`. Hardware remains
NOT_ADMITTED pending page-baseline establishment, independent controller/GIC/
callback snapshot and restore, CRC validation and a bounded physical wrapper.
Next implement/test the state lifecycle offline. Do not infer that a mocked
ownership assertion proves actual IRQ exclusion or that lower-page cleanup
restores an unknown initial SPD page.

## Peripheral/software state lifecycle candidate

`spd_xiicps_state.h` takes a read-only snapshot only after caller ownership/no-GIC
assertion plus quiet controller/empty FIFO/zero transfer/zero IRQ status/no HOLD
or clear-FIFO command/zero driver byte counts. It saves CR, timeout, peripheral
interrupt mask and the full XIicPs instance including callback/ref. Restore
requires inactive/non-poisoned adapter and quiet controller, disables peripheral
IRQs, restores registers/software, restores peripheral mask and independently
checks register readback/quiet state. Snapshot and adapter are consumed after
restore; mismatched readback poisons. There is no reset/FIFO-clear workaround.

Integration model restores original non-null callback/ref and registers after
success or mismatch. Error/pending states refuse restore without writes. Seven
dirty/unowned snapshot refusals, wrong readback and double restore controls PASS
with ASan/UBSan. AArch64 header compile against real BSP PASS. Evidence:
`evidence/spd-state-lifecycle-2026-10-22`. This does not snapshot or restore GIC
routing, prove ownership, restore unknown SPD page or guarantee cleanup after
peripheral failure. Those remain prerequisites for a physical wrapper.

For page discovery, [Linux EE1004 source](https://kernel.googlesource.com/pub/scm/linux/kernel/git/netdev/net/+/761c6d7ec820f123b931e7b8ef7ec7c8564e450f/drivers/misc/eeprom/ee1004.c)
uses a dedicated read of the page-select address: ACK/page0 versus address-NACK/
page1, with other errors propagated. This is protocol-specific behavior, not
permission to reinterpret generic EEPROM/controller NACK. Current adapter still
poisons on all NACK. Next isolate page-query classification and restoration with
independent route/device admission and exact error events, then model the whole
lifecycle before hardware. No source from Linux is copied into firmware here.

## Dedicated EE1004 page classifier (offline)

`spd_page.h` classifies only a one-byte read at0x36, requiring external exclusive
route and independent SPD identity evidence. Page0 requires exactly successful
receive with allowed raw completion/data IRQs and one byte. Page1 requires zero
bytes, exact raw address-NACK and AMD NACK|ERROR events. Busy/FIFO data, timeout,
arbitration, mixed completion/NACK, wrong address/count or absent identity
return UNKNOWN. The returned byte value does not encode the page.

Saved page0/1 proposes select address0x36/37; UNKNOWN refuses. Restoration may
only be confirmed when a later independently classified response equals the
saved page. This does **not** implement selection or actual restoration. The
model executes actual AMD MasterRecv+ISR for both page responses, with ownership/
identity explicitly asserted by the fixture. Pure C controls reject11uncertain
responses; ASan/UBSan and AArch64 test-object compile PASS.

```sh
cc -std=c11 -Wall -Wextra -Werror -fsanitize=address,undefined \
  -I"$BSP/include" tests/test_spd_page.c -o /tmp/artiq-test-spd-page
/tmp/artiq-test-spd-page
```

Evidence: `evidence/spd-page-classification-2026-10-22`. General adapter NACK
poisoning is unchanged. Actual query lifecycle (including zero received bytes
left pending after protocol NACK), route/device evidence, page selection/
confirmation, GIC restoration, CRC and physical wrapper remain open. Next bind
a bounded dedicated query lifecycle rather than adding a global NACK exception.

## Bounded dedicated page operations candidate

`spd_page_transfer.h` uses actual AMD nonblocking send/receive/ISR for query0x36
or one zero-byte selection at0x36/37. Zero-initialize the operation object once;
failed/active objects refuse another begin. Caller must retain it (callback
reference) until completion or outer restoration. Each operation has100ms/10000
poll budget and rejects clock reversal/overflow. Exclusive/no-GIC and independent
identity remain external evidence, required before any write/callback change.

For the exact admitted page1 query only, zero-byte address-NACK can be retired
after idle/empty FIFO/clear ISR/no HOLD and exact residual hardware count1.
Peripheral IRQs are disabled, unused transfer count set0 and read back, software
receive counters retired. No abort/reset/FIFO clear/retry or generic NACK waiver.
Other failures retain active state and require outer restoration. A selection
ACK only proves transmission completion: page remains UNKNOWN until a later
query confirms the requested/saved page.

Actual AMD model passes query/select0/query/restore/query for initial pages0and1,
plus8fault scenarios (no events, arbitration, mixed completion/NACK, wrong
remaining count, failed count retirement, ignored selection despite ACK, select
NACK and stuck RXDV). Missing identity rejects before writes; failed objects
refuse reuse. Existing capture/state controls retained. ASan/UBSan and real-BSP
AArch64 header compile PASS. Evidence: `evidence/spd-page-lifecycle-2026-10-22`.

This still does not combine page lifecycle, data reader and controller snapshot
into one recovery transaction or establish physical identity/GIC exclusion/CRC.
Next offline compose that lifecycle and test restoration on every exit before
creating a physical wrapper. Hardware remains NOT_ADMITTED.

## Composed capture/restoration session candidate

`spd_session.h` composes snapshot→saved-page query→lower-page select/query→
dual128-byte read→saved-page select/query→controller/software restore.
A session is zero-initialized once, cannot be reused and must remain alive until
outer recovery because callbacks reference its storage. Overall bound3s/200000
polls supplements per-operation bounds; callbacks/MMIO still require platform
progress. External identity/ownership/no-GIC preconditions remain mandatory.

Results distinguish matching `READS_RESTORED` (still no CRC),
`FAILED_RESTORED` for a mismatch/failed lower-page confirmation with verified
restoration, and `OUTER_RESTORE_REQUIRED` for active/poisoned operations or
unconfirmed page/controller restoration. It does not force cleanup onto a failed
bus. A dirty initial snapshot/missing evidence is NOT_ADMITTED. No automatic retry.

Actual AMD MMIO model passes14composed cases (both original pages times normal,
payload mismatch, data NACK, controller readback failure, ignored restore select,
ignored lower-page select and initial-query arbitration), preserving earlier
component controls. ASan/UBSan and actual-BSP AArch64 header compilation PASS.
Evidence: `evidence/spd-composed-session-2026-10-22`. A select ignored while the
requested page is already selected is harmless only when the later query proves
the required state. Wrong saved-page confirmation is never hidden by successful
controller restoration.

Next CRC validation and a concrete independent route/device/GIC admission before
linking a diagnostic and preparing the bounded hardware wrapper. No physical
SPD/CRC/DDR test or hardware admission is claimed by these models.

## Base-block CRC validation

Host `check_ddr4_spd_crc.py` uses the standard-library CRC primitive, initial0/
polynomial0x1021, covering bytes0..125 and comparing little-endian126..127.
Reference: [i2c-tools decode-dimms](https://kernel.googlesource.com/pub/scm/utils/i2c-tools/i2c-tools/+/refs/heads/master/eeprom/decode-dimms),
reviewed blob76823459da4693fe5a7ecf5b6e3aa092f280918a. Supported DDR4 profile
requires byte0 bit7 clear; other coverage profiles reject rather than silently
using DDR3 shortened coverage. This does not validate module-block CRC.

```sh
python3 scripts/check_ddr4_spd_crc.py --spd CAPTURE.bin --output FRESH-crc.json
python3 scripts/decode_ddr4_spd.py --require-crc \
  --spd CAPTURE.bin --output FRESH-geometry.json
python3 scripts/compare_ddr_geometry.py --require-crc --spd CAPTURE.bin \
  --snapshot DDRC-SNAPSHOT.log --output FRESH-comparison.json
```

Bad CRC emits FAIL/exit1 from checker; required decoder/comparison raises and
rejects. Legacy exploratory mode without `--require-crc` remains explicitly
NOT_VERIFIED; it is not an acquisition acceptance path. A physical wrapper must
require CRC after matching captures and verified restoration. The C session's
READS_RESTORED flag still certifies transport/restoration only.

Four new test methods cover known primitive vector, all1024single-bit base
corruptions, endian/coverage/profile failures and downstream/CLI rejection;
five existing SPD/geometry controls PASS. Synthetic fixtures/results remain
explicitly identified in `evidence/spd-base-crc-2026-10-22`. No actual SPD dump
or physical memory capacity/integrity evidence is created by CRC tests.

## First physical SPD acquisition: instrument Piotr's existing FSBL

The [Digilent manual](https://digilent.com/reference/programmable-logic/genesys-zu/reference-manual)
confirms SPD directly on MIO8/9 via I2C1, matching Piotr's PS settings. BSP
I2C1 base0xff030000 and encoded interrupt0x4012 decode via AMD wrapper to SPI50.
This is configuration/source evidence; live IRQ state is not inferred.

For the first physical dump, reuse Piotr's existing FSBL reader/training rather
than waiting for deployment of the new standalone reader. The diagnostic FSBL
adds only UART logging after original SPD read success. It makes no extra I2C
transactions and preserves page selection/training behavior. This route does
not require installing the candidate manual-ISR adapter or changing its GIC
ownership rules. The adapter remains offline for independent diagnostics.

Build an isolated diagnostic (default boot build remains unchanged):

```sh
FSBL_SPD_DUMP=1 scripts/build_boot_firmware.sh XSA FRESH_OUTPUT ARM_GNU_PREFIX
```

Run inside the existing Vivado container as for the normal firmware build.
Instrumentation refuses changed Piotr source by hash and writes fresh source,
unified diff and manifest. No original checkout/shared qualified BSP is edited.
FSBL/PMU build PASS in `build-vivado/fsbl-spd-dump-20261022`; linked ELF contains
the dynamic DDR call. Source diff/hashes/compressed build log in
`evidence/fsbl-spd-dump-build-2026-10-22`.

`decode_fsbl_spd_log.py --log UART --output FRESH` requires exactly one complete
128-byte frame/eight ordered rows, later FSBL completion, valid base CRC and
supported geometry. It writes raw bytes plus report. Three controls compile the
actual injected C emitter and decode synthetic data, reject malformed/truncated/
CRC-bad/no-completion frames, and reject changed original source. No physical
SPD dump yet. Next add the diagnostic FSBL to a bounded candidate runtime window
with strict UART parsing and full normal restoration; do not package it as the
normal SD release or flash it.

## Diagnostic FSBL wrapper and first physical capture

```sh
python3 scripts/test_candidate_runtime_hw.py --fsbl-spd \
  --manifest evidence/fsbl-spd-capture-plan-2026-10-22/inputs.json \
  --output FRESH_OUTPUT
```

Default is offline preflight. Execution additionally needs `--execute`, verified
server/UART/interface and the shared Genesys lease (enforced by wrapper).
FSBL, PMU, PS setup and execution/parser scripts are pinned. OCM/extended/fault
modes cannot be combined with this diagnostic mode. Strict SPD extraction/CRC
runs after candidate load and before normal debug/Ethernet checks; failures
always enter baseline restoration under the same lease. Do not run with
insufficient disk space; an explicit space admission check is the next fix.

First physical window captured128bytes with valid CRC0x2e87:4GiB, single rank,
64-bit bus, x16devices,16row/10column/2bank/1group bits. All7geometry fields
match the earlier DDRC snapshot. Data hex/raw UART/provenance:
`evidence/fsbl-spd-capture-hardware-2026-10-22`. This is not a full memory test.

Initial window remains FAIL: shared data disk filled, Vivado could not launch
cs_server/create .Xil, and its first restoration attempt failed. Only this
thread's completed diagnostic build was relocated to root storage with verified
copy and original-path symlink (4285entries preserved). A separate exclusive
recovery window restored normal ARTIQ192.168.2.3; physical RTIO/debug/Ethernet
PASS. Diagnostic FSBL is not release-qualified or selected as normal default.
No SD/flash/OTP/Si changes. Next offline add pre-reset free-space admission, then
continue DDR master/window/test-interval planning using the physical SPD evidence.

## Storage admission before any new runtime load

Following the observed ENOSPC incident, candidate wrapper checks free bytes and
inodes before creating execution output/claiming HW, then rechecks under the
Genesys lease. Direct runtime loader checks before opening UART/resetting.
Roles: output directory, working directory (.Xil), launcher-bound AMD home/tmp
and host/tmp. The launcher explicitly uses shared AMD TMPDIR, so moving output
alone does not move all temporary writes. Symlinks/future directories resolve to
the existing backing filesystem ancestor.

Operational headroom policy: at least512MiB available and1024available inodes on
every relevant filesystem. This is an engineering admission budget, not a
reservation or guarantee against another process consuming disk after the check.
No force/bypass switch or cleanup/deletion is part of admission. If space shrinks
after hardware mutation, restoration can still fail and must be reported.

```sh
python3 scripts/check_hw_storage.py --output-directory FUTURE_OUTPUT
```

Metadata only, no hardware lease/device access required. Current shared disk
fails admission; normal ARTIQ remains unchanged. Five storage/order controls plus
six lifecycle/three SPD wrapper controls PASS. Read-only actual filesystem report:
`evidence/hw-storage-admission-2026-10-22`.

Execution/parser pins changed; use the new diagnostic manifest
`evidence/fsbl-spd-capture-plan-v2-2026-10-22/inputs.json` for future attempts.
Its artifact-only offline preflight PASS is intentionally separate from storage
admission. Historical manifest/evidence remain unchanged. Next inventory/relocate
only this thread's completed build outputs with byte verification and retained
paths, then recheck storage. DDR master/window planning can continue offline.

## Completed-build storage relocation —2026-10-22

Six explicitly allowlisted completed outputs were copied to root-disk
`/home/codex-hil/.local/state/artiq-builds`. The tool inventories hashes, modes
and symlink targets, copies without dereferencing links, checks both unchanged
source and destination, publishes a verification report, then retains original
paths through symlinks. A failed link publication rolls the original directory
back; a bad copy never removes the original. New output/report paths are required.
No other project, shared toolchain, original checkout or device was changed.

22517inventory entries verified. Old selected normal/diagnostic artifact hashes
and layouts still PASS through original paths. Shared disk free space increased
from approximately89MiB to604MiB and the512MiB/inode storage gate now PASSes.
This remains a point-in-time result; every hardware window must recheck it.
Evidence and full compressed inventories:
`evidence/completed-build-relocation-2026-10-22`. Three controls cover exact
byte/link/mode preservation, corrupt-copy rejection and link-publication rollback.

The relocation tool defaults to plan-only and accepts only the six reviewed
build names; it is not a generic shared-workspace cleanup tool. Already moved
symlink paths reject a second relocation. Hardware was not accessed. Next one
bounded diagnostic FSBL SPD window using the v2 manifest can confirm the
complete candidate/parse/debug/Ethernet/restoration sequence after the earlier
disk-full failure; all existing shared-lease and storage checks still apply.

### Complete diagnostic FSBL SPD/runtime window PASS —2026-10-22

The v2 pinned candidate completed under the shared Genesys lease (138.067s),
with storage admission before reset. Physical SPD base bytes exactly repeat the
first capture: SHA256 ab0343bdadbb16c6dbf91e7066817f67fcaaae28ec03be36c088e5481fb2bf83,
stored/computed CRC 0x2e87, reported 4GiB/one rank/64-bit bus/x16 devices.
Candidate and restored normal runtime both passed physical TTL/CoreDMA, standard
analyzer/MonInj clients, analyzer ring wrap, 20/20 ICMP and five byte-exact TCP
echo connections. Normal runtime restored at192.168.2.3; lease released.
Evidence: `evidence/fsbl-spd-complete-hardware-2026-10-22` (raw logs compressed;
summary records original raw hashes). Earlier disk-full FAIL remains preserved.
This validates the diagnostic FSBL handoff, not full DDR integrity, high-window
alias freedom or a promoted boot release. No Kasli/Si/SD/flash/OTP writes.
Next offline work: define trained-DDR OCM handoff, cache/master ownership and
explicit disjoint low/high test intervals before destructive-test admission.

## Sparse DDR alias plan prepared offline —2026-10-22

`scripts/plan_ddr_alias_probes.py --output /path/to/fresh-plan.json` enumerates
64-byte probes at logical address-bit offsets6..31 plus low/high boundaries.
Logical capacity offsets map explicitly into `[0,0x80000000)` and
`[0x800000000,0x880000000)`; no probe touches the intervening MMIO gap.
Distinct tags must be written across all probes before any verification, then
repeated with complements: an immediate write/read of each location would miss
aliasing. These are sparse logical-address checks, not full DRAM wiring coverage
or an integrity/stress test. Three boundary/bit-coverage/rejection controls PASS.
Evidence: `evidence/ddr-alias-plan-2026-10-22`. No hardware accessed.

Execution remains NOT_ADMITTED. The existing cold OCM loader skips DDR training
and cannot be reused unchanged. Next prepare a trained-DDR OCM handoff with
explicit EL3/EL1 cache policy and other-core/PS-DMA/PL-master ownership evidence.
Physical SPD and controller agreement do not substitute for these conditions.
Normal runtime remains at the last validated192.168.2.3 baseline.
