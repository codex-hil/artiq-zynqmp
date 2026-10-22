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
